from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from typing import Any
import json
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

import sympy as sp

from .math_engine import MathEngine
from .graph_generator import GraphGenerator
from .models import Calculation, Graph, UserProfile
from .natural_parser import NaturalLanguageParser
from .advanced_math_parser import AdvancedMathParser, parse_math_text
from .step_serializer import StepSerializer, serialize_result_with_steps
from .services.cerebras_text_solver import (
    cerebras_text_solver,
    CerebrasAPIError,
    CerebrasConfigError,
    CerebrasResponseError,
)
from .services.ai_explainer import (
    ai_explainer,
    AIExplanationAPIError,
    AIExplanationConfigError,
    AIExplanationResponseError,
)

logger = logging.getLogger(__name__)

math_engine = MathEngine()
graph_generator = GraphGenerator()
# Small thread pool used to enforce a hard timeout on AI explanations.
_ai_executor = ThreadPoolExecutor(max_workers=2)


def _expressions_equivalent(latex_a: str, latex_b: str) -> bool:
    """
    Compare two LaTeX expressions for mathematical equivalence using SymPy.
    """
    if not latex_a or not latex_b:
        return False
    try:
        expr_a = math_engine.parse_latex(latex_a)
        expr_b = math_engine.parse_latex(latex_b)
        # Use SymPy simplification to check equivalence
        return sp.simplify(expr_a - expr_b) == 0
    except Exception as e:
        logger.warning("Failed to compare expressions '%s' and '%s': %s", latex_a, latex_b, e)
        return False


def _build_fallback_response(original_input: str, error: Exception) -> JsonResponse:
    """
    Build a unified fallback response that instructs the frontend to redirect
    the user to the Text (AI) tab. This is used when a deterministic solver
    fails due to parsing, syntax, or runtime errors.
    """
    error_type = type(error).__name__ if isinstance(error, Exception) else "SolverError"
    message = str(error) if hasattr(error, "__str__") else "Solver failed"

    payload = {
        "status": "fallback",
        "target_tab": "text",
        "original_input": original_input or "",
        "error_type": error_type,
        "error_message": message,
    }
    # Always return HTTP 200 so the frontend can handle the fallback smoothly.
    return JsonResponse(payload)


def index(request):
    """Main page"""
    return render(request, 'solver/index.html')


def about(request):
    """About page"""
    return render(request, 'solver/about.html')


def documentation(request):
    """Documentation page"""
    return render(request, 'solver/documentation.html')


@csrf_exempt
@require_http_methods(["POST"])
def solve(request):
    """API endpoint for solving math problems"""
    try:
        data = json.loads(request.body)
        
        # Input validation
        if not data:
            raise ValidationError("Request body cannot be empty")
            
        operation = data.get('operation')
        expression = data.get('expression', '').strip()
        original_input = data.get('original_input', expression)
        save_history = data.get('save_history', True)

        # Input length limits to prevent DoS
        if len(expression) > 1000:
            raise ValidationError("Expression too long (max 1000 characters)")
        if len(original_input) > 1000:
            raise ValidationError("Input too long (max 1000 characters)")

        if not operation:
            raise ValidationError("Operation is required")

        if not expression and operation not in ['text', 'matrix']:
            raise ValidationError("Expression is required")
        
        # Validate operation
        valid_operations = ['solve', 'derivative', 'integral', 'limit', 'simplify', 'factor', 'expand', 'text', 'matrix']
        if operation not in valid_operations:
            raise ValidationError(f"Invalid operation: {operation}")
        
        result = None
        
        if operation == 'solve':
            result = math_engine.solve_equation(expression)
        elif operation == 'derivative':
            variable = data.get('variable', 'x').strip()
            if not variable:
                raise ValidationError("Variable is required for derivative")
            try:
                order = int(data.get('order', 1))
                if order < 1 or order > 10:
                    raise ValidationError("Order must be between 1 and 10")
            except (ValueError, TypeError):
                raise ValidationError("Order must be a valid integer")
            result = math_engine.derivative(expression, variable, order)
        elif operation == 'integral':
            variable = data.get('variable', 'x').strip()
            if not variable:
                raise ValidationError("Variable is required for integral")
            definite = data.get('definite', False)
            if definite:
                try:
                    lower = float(data.get('lower', 0))
                    upper = float(data.get('upper', 1))
                    if lower >= upper:
                        raise ValidationError("Lower bound must be less than upper bound")
                except (ValueError, TypeError):
                    raise ValidationError("Bounds must be valid numbers")
                result = math_engine.integral(expression, variable, True, lower, upper)
            else:
                result = math_engine.integral(expression, variable, False)
        elif operation == 'limit':
            variable = data.get('variable', 'x').strip()
            if not variable:
                raise ValidationError("Variable is required for limit")
            point = data.get('point', '0').strip()
            side = data.get('side', '+')
            if side not in ['+', '-', 'both']:
                side = '+'
            result = math_engine.limit(expression, variable, point, side)
        elif operation == 'matrix':
            # Matrix operations
            matrix_op = data.get('matrix_operation', 'determinant')
            valid_matrix_ops = ['determinant', 'inverse', 'transpose', 'rref']
            if matrix_op not in valid_matrix_ops:
                raise ValidationError(f"Invalid matrix operation: {matrix_op}")
            
            # Parse matrix from expression (e.g., "[[1,2],[3,4]]")
            try:
                import ast
                matrix_data = ast.literal_eval(expression)
                if not isinstance(matrix_data, list) or not all(isinstance(row, list) for row in matrix_data):
                    raise ValidationError("Matrix must be a 2D array, e.g., [[1,2],[3,4]]")
            except (ValueError, SyntaxError):
                raise ValidationError("Invalid matrix format. Use [[1,2],[3,4]] format")
            
            # Perform matrix operation
            result = math_engine.matrix_operations(matrix_op, matrix_data)
        elif operation in ['simplify', 'factor', 'expand']:
            result = getattr(math_engine, operation)(expression)
        elif operation == 'text':
            # Natural language processing
            if not original_input:
                raise ValidationError("Text input is required for natural language processing")
            try:
                parsed = NaturalLanguageParser().parse(original_input)
                if not parsed:
                    raise ValidationError("Could not parse the natural language input")
                
                operation = parsed['operation']
                expression = parsed['expression']
                result = getattr(math_engine, operation)(expression)
                original_input = original_input
            except Exception as e:
                logger.error(f"Natural language parsing failed: {e}")
                raise ValidationError("Failed to parse natural language input")
        
        if result and 'error' in result:
            logger.warning(f"Math engine error: {result['error']}")
            return _build_fallback_response(original_input, Exception(result['error']))
        
        # Save to history if requested and user is authenticated
        if save_history and request.user.is_authenticated and result:
            try:
                Calculation.objects.create(
                    user=request.user,
                    operation_type=operation,
                    original_input=original_input,
                    parsed_math_expression=expression,
                    result=result.get('result', ''),
                    latex_result=result.get('latex', ''),
                    steps=result.get('steps', [])
                )
            except Exception as e:
                logger.error(f"Failed to save calculation: {e}")
        
        # Normalize result to ensure all fields are properly serialized
        normalized_result = serialize_result_with_steps(result)
        
        response_data = {
            'result': normalized_result.get('result', ''),
            'latex': normalized_result.get('latex', ''),
            'steps': normalized_result.get('steps', []),
            'original_expression': expression
        }
        
        # Add deterministic, engine-based explanation if available
        if operation in ['solve', 'derivative', 'integral', 'limit', 'simplify', 'factor', 'expand']:
            try:
                detailed = math_engine.get_detailed_explanation(
                    operation, expression, result.get('result', ''),
                    data.get('variable', 'x'),
                    data.get('definite', False),
                    data.get('lower'),
                    data.get('upper'),
                    data.get('point'),
                    data.get('side', '+')
                )
                response_data['detailed_explanation'] = detailed
            except Exception as e:
                logger.error(f"Failed to generate detailed explanation: {e}")

            # Optionally enrich with AI-generated explanations, keeping the
            # math engine as the source of truth.
            canonical_latex = normalized_result.get('latex', '')
            engine_steps = normalized_result.get('steps', [])
            # Enable AI explanations for all math operation types handled here.
            enable_ai_explanation = operation in [
                'solve',
                'derivative',
                'integral',
                'limit',
                'simplify',
                'factor',
                'expand',
            ]

            if enable_ai_explanation and canonical_latex and ai_explainer.is_configured:
                def _ai_job() -> Any:
                    """
                    Run the AI explanation pipeline and return serialized steps,
                    or None if explanations should not be applied.
                    """
                    try:
                        # First AI attempt
                        ai_result = ai_explainer.generate_explanation(
                            problem_text=original_input,
                            operation=operation,
                            canonical_result_latex=canonical_latex,
                            engine_steps=engine_steps,
                        )

                        final_matches = _expressions_equivalent(
                            canonical_latex, ai_result.final_answer_latex
                        )

                        # If mismatch, retry once with explicit correction context
                        if not final_matches:
                            logger.warning(
                                "AI explanation mismatch for operation %s. "
                                "Expected %s, got %s. Retrying once.",
                                operation,
                                canonical_latex,
                                ai_result.final_answer_latex,
                            )
                            ai_result_retry = ai_explainer.generate_explanation(
                                problem_text=original_input,
                                operation=operation,
                                canonical_result_latex=canonical_latex,
                                engine_steps=engine_steps,
                                previous_ai_final_latex=ai_result.final_answer_latex,
                            )
                            if _expressions_equivalent(
                                canonical_latex, ai_result_retry.final_answer_latex
                            ):
                                ai_result = ai_result_retry
                                final_matches = True
                            else:
                                logger.error(
                                    "AI explanation second attempt still mismatched for operation %s. "
                                    "Engine result will be used without AI steps.",
                                    operation,
                                )

                        # Only attach AI steps if the final result matches the engine.
                        if final_matches:
                            ai_steps_serialized = []
                            for idx, step in enumerate(ai_result.steps, start=1):
                                ai_steps_serialized.append(
                                    {
                                        'title': f"Step {step.step_number}",
                                        'latex': step.latex,
                                        'explanation': step.explanation,
                                    }
                                )
                            return ai_steps_serialized
                        return None
                    except (AIExplanationConfigError, AIExplanationAPIError, AIExplanationResponseError) as e:
                        # Log but do not fail the main solve pipeline
                        logger.error("AI explanation generation failed: %s", e)
                        return None
                    except Exception as e:
                        logger.error("Unexpected error during AI explanation generation: %s", e)
                        return None

                future = _ai_executor.submit(_ai_job)
                try:
                    ai_steps = future.result(timeout=10)
                    if ai_steps:
                        # Replace canonical steps with verified AI explanations
                        response_data['steps'] = ai_steps
                except FuturesTimeoutError:
                    # If AI takes too long, fall back to engine steps
                    logger.error(
                        "AI explanation generation exceeded 10 seconds for operation %s. "
                        "Falling back to step engine only.",
                        operation,
                    )
                    future.cancel()
        
        return JsonResponse(response_data)
        
    except ValidationError as e:
        logger.warning(f"Validation error in solve: {e}")
        return _build_fallback_response(data.get('original_input', data.get('expression', '')), e)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in solve request")
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in solve: {e}")
        original_raw = None
        try:
            body = json.loads(request.body or b"{}")
            original_raw = body.get('original_input') or body.get('expression', '')
        except Exception:
            original_raw = ''
        return _build_fallback_response(original_raw, e)


@csrf_exempt
@require_http_methods(["POST"])
def solve_text_with_cerebras(request):
    """
    API endpoint for solving text-based (word) math problems using Cerebras.

    This endpoint is intentionally separate from the main /api/solve/ endpoint
    to keep AI-specific behavior isolated from the core symbolic math engine.
    """
    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in solve_text_with_cerebras request")
            return JsonResponse(
                {
                    "error": {
                        "type": "INVALID_JSON",
                        "message": "Invalid JSON format",
                    }
                },
                status=400,
            )

        text = (data.get("text") or "").strip()

        if not text:
            raise ValidationError("Text problem is required")
        if len(text) > 4000:
            # Keep an upper bound to avoid accidental abuse / excessive token usage
            raise ValidationError("Text too long (max 4000 characters)")

        # Delegate to the isolated Cerebras service.
        ai_result = cerebras_text_solver.solve_text_problem(text)

        # The service already returns the structured JSON required by the spec,
        # so we simply forward it to the frontend.
        return JsonResponse(ai_result)

    except ValidationError as e:
        logger.warning("Validation error in solve_text_with_cerebras: %s", e)
        return JsonResponse(
            {
                "error": {
                    "type": "VALIDATION_ERROR",
                    "message": str(e),
                }
            },
            status=400,
        )
    except CerebrasConfigError as e:
        logger.error("Cerebras configuration error: %s", e)
        return JsonResponse(
            {
                "error": {
                    "type": "CEREBRAS_CONFIG_ERROR",
                    "message": str(e),
                }
            },
            status=500,
        )
    except CerebrasResponseError as e:
        logger.error("Cerebras returned malformed response: %s", e)
        return JsonResponse(
            {
                "error": {
                    "type": "CEREBRAS_RESPONSE_ERROR",
                    "message": "AI returned an unexpected response. Please try again.",
                }
            },
            status=502,
        )
    except CerebrasAPIError as e:
        logger.error("Cerebras API error: %s", e)
        return JsonResponse(
            {
                "error": {
                    "type": "CEREBRAS_API_ERROR",
                    "message": "Failed to contact the AI solver. Please try again later.",
                }
            },
            status=502,
        )
    except Exception as e:
        logger.error("Unexpected error in solve_text_with_cerebras: %s", e)
        return JsonResponse(
            {
                "error": {
                    "type": "INTERNAL_SERVER_ERROR",
                    "message": "Internal server error",
                }
            },
            status=500,
        )


@csrf_exempt
@require_http_methods(["POST"])
def generate_graph(request):
    """API endpoint for generating graphs"""
    try:
        data = json.loads(request.body)
        
        # Input validation
        expression = data.get('expression', '').strip()
        if not expression:
            raise ValidationError("Expression is required")
        if len(expression) > 1000:
            raise ValidationError("Expression too long (max 1000 characters)")
        
        x_min = data.get('x_min', -10)
        x_max = data.get('x_max', 10)
        y_min = data.get('y_min')
        y_max = data.get('y_max')
        
        # Validate numeric ranges
        try:
            x_min = float(x_min)
            x_max = float(x_max)
            if x_min >= x_max:
                raise ValidationError("x_min must be less than x_max")
        except (ValueError, TypeError):
            raise ValidationError("x_min and x_max must be valid numbers")
        
        if y_min is not None:
            try:
                y_min = float(y_min)
            except (ValueError, TypeError):
                y_min = None
        
        if y_max is not None:
            try:
                y_max = float(y_max)
            except (ValueError, TypeError):
                y_max = None
        
        if y_min is not None and y_max is not None and y_min >= y_max:
            raise ValidationError("y_min must be less than y_max")
        
        # Generate graph
        try:
            x_range = (x_min, x_max)
            y_range = (y_min, y_max) if y_min is not None and y_max is not None else None
            image_data = graph_generator.generate_plot(
                expression, x_range, y_range
            )
        except Exception as e:
            logger.error(f"Graph generation failed: {e}")
            raise ValidationError("Failed to generate graph. Please check your expression.")
        
        # Save to history if user is authenticated
        if request.user.is_authenticated:
            try:
                Graph.objects.create(
                    user=request.user,
                    expression=expression,
                    x_min=x_min,
                    x_max=x_max,
                    y_min=y_min,
                    y_max=y_max
                )
            except Exception as e:
                logger.error(f"Failed to save graph: {e}")
        
        return JsonResponse({'image': image_data})
        
    except ValidationError as e:
        logger.warning(f"Validation error in generate_graph: {e}")
        return _build_fallback_response(
            data.get('expression', '') if 'data' in locals() else '',
            e,
        )
    except json.JSONDecodeError:
        logger.error("Invalid JSON in generate_graph request")
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in generate_graph: {e}")
        expr = ''
        try:
            body = json.loads(request.body or b"{}")
            expr = body.get('expression', '')
        except Exception:
            expr = ''
        return _build_fallback_response(expr, e)


@csrf_exempt
@require_http_methods(["POST"])
def parse_natural_language(request):
    """API endpoint for parsing natural language math problems"""
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()

        if not text:
            raise ValidationError("Text is required")
        if len(text) > 2000:
            raise ValidationError("Text too long (max 2000 characters)")
        
        parser = NaturalLanguageParser()
        result = parser.parse(text)
        
        if not result:
            # Fall back to AI text solver instead of returning an error.
            return _build_fallback_response(text, Exception("Could not parse the text"))
        
        return JsonResponse(result)
        
    except ValidationError as e:
        logger.warning(f"Validation error in parse_natural_language: {e}")
        return _build_fallback_response(
            data.get('text', '') if 'data' in locals() else '',
            e,
        )
    except json.JSONDecodeError:
        logger.error("Invalid JSON in parse_natural_language request")
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in parse_natural_language: {e}")
        txt = ''
        try:
            body = json.loads(request.body or b"{}")
            txt = body.get('text', '')
        except Exception:
            txt = ''
        return _build_fallback_response(txt, e)


@login_required
@login_required
@require_http_methods(["GET"])
def get_history(request):
    """Get calculation history for authenticated user"""
    try:
        calculations = Calculation.objects.filter(user=request.user).order_by('-created_at')[:50]
        
        history = []
        for calc in calculations:
            history.append({
                'id': calc.id,
                'operation': calc.operation_type,
                'original_input': calc.original_input,
                'expression': calc.parsed_math_expression,
                'result': calc.result,
                'latex': calc.latex_result,
                'steps': calc.steps,
                'created_at': calc.created_at.isoformat()
            })
        
        return JsonResponse({'history': history})
        
    except Exception as e:
        logger.error(f"Error in get_history: {e}")
        return JsonResponse({'error': 'Failed to retrieve history'}, status=500)


@login_required
def profile(request):
    """User profile page"""
    try:
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        if request.method == 'POST':
            theme = request.POST.get('theme', 'light')
            if theme in ['light', 'dark']:
                user_profile.theme_preference = theme
                user_profile.save()
                messages.success(request, 'Theme preference updated!')
        
        context = {
            'user_profile': user_profile,
            'calculations_count': Calculation.objects.filter(user=request.user).count(),
            'graphs_count': Graph.objects.filter(user=request.user).count()
        }
        return render(request, 'solver/profile.html', context)
        
    except Exception as e:
        logger.error(f"Error in profile: {e}")
        messages.error(request, 'Failed to load profile')
        return redirect('/')


@login_required
def history(request):
    """History page for authenticated users"""
    return render(request, 'solver/history.html')


def register(request):
    """User registration"""
    try:
        if request.method == 'POST':
            username = request.POST.get('username')
            email = request.POST.get('email')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            # Validation
            if not username or not email or not password1:
                messages.error(request, 'All fields are required')
                return render(request, 'registration/register.html')
            
            if password1 != password2:
                messages.error(request, 'Passwords do not match')
                return render(request, 'registration/register.html')
            
            if len(password1) < 8:
                messages.error(request, 'Password must be at least 8 characters long')
                return render(request, 'registration/register.html')

            # Additional password complexity checks
            if not any(c.isupper() for c in password1):
                messages.error(request, 'Password must contain at least one uppercase letter')
                return render(request, 'registration/register.html')

            if not any(c.islower() for c in password1):
                messages.error(request, 'Password must contain at least one lowercase letter')
                return render(request, 'registration/register.html')

            if not any(c.isdigit() for c in password1):
                messages.error(request, 'Password must contain at least one digit')
                return render(request, 'registration/register.html')
            
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists')
                return render(request, 'registration/register.html')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists')
                return render(request, 'registration/register.html')
            
            # Create user
            user = User.objects.create_user(username=username, email=email, password=password1)
            UserProfile.objects.create(user=user)
            
            # Auto login
            user = authenticate(username=username, password=password1)
            if user:
                login(request, user)
                return redirect('/profile/')
            
            return redirect('/')
        
        return render(request, 'registration/register.html')
        
    except Exception as e:
        logger.error(f"Error in register: {e}")
        messages.error(request, 'Registration failed. Please try again.')
        return render(request, 'registration/register.html')


@login_required
@require_http_methods(["POST"])
def delete_calculation(request, calc_id):
    """Delete a calculation from history"""
    try:
        calculation = Calculation.objects.get(id=calc_id, user=request.user)
        calculation.delete()
        return JsonResponse({'success': True})
    except Calculation.DoesNotExist:
        return JsonResponse({'error': 'Calculation not found'}, status=404)
    except Exception as e:
        logger.error(f"Error deleting calculation: {e}")
        return JsonResponse({'error': 'Failed to delete calculation'}, status=500)