from typing import Callable, Any
import inspect
import datetime

def debug(*, output: Callable[[str], Any] = print, catch_exceptions: bool = False) -> Callable[[Callable], Callable]:
    """
    A debugging decorator that logs function calls with detailed parameter information.
    This decorator traces function execution by capturing and displaying:
    - All positional-only, positional-or-keyword, keyword-only arguments
    - Variable positional (*args) and keyword (**kwargs) parameters
    - Parameter types and values
    - Return values and exceptions
    - Execution time for the function call
    Args:
        output: Callable to handle debug messages (default: print)
        catch_exceptions: If True, suppress exceptions and return None; if False, re-raise them
    Returns:
        A wrapper function that logs function invocation details before and after execution
    """
    def wrapper(func: Callable) -> Callable:

        def inner(*args, **kwargs):

            fnc_sig = inspect.signature(func)
            fnc_params = fnc_sig.parameters

            def params(kind: Any) -> list[str]:
                return [param.name for param in fnc_params.values() if param.kind == kind]
            
            def var_params(kind: Any) -> str | None:
                return next((param.name for param in fnc_params.values() if param.kind == kind), None)

            pos_only_params = params(inspect.Parameter.POSITIONAL_ONLY)
            pos_or_kw_params = params(inspect.Parameter.POSITIONAL_OR_KEYWORD)
            kw_only_params = params(inspect.Parameter.KEYWORD_ONLY)
            pos_var_param = var_params(inspect.Parameter.VAR_POSITIONAL)
            kw_var_param = var_params(inspect.Parameter.VAR_KEYWORD)

            fnc_sig_args = fnc_sig.bind(*args, **kwargs)
            fnc_sig_args.apply_defaults()
            fnc_args = dict(fnc_sig_args.arguments)
                
            def view_param(name: str, var: bool = False) -> str:
                param = fnc_params[name]
                value = fnc_args[name]
                match (var, param.annotation is inspect._empty):
                    case (True, True): return f"{name} = {value!r}"
                    case (True, False): return f"{name}: {param.annotation.__name__} = {value!r}"
                    case (False, True): return f"{name} = {type(value).__name__}[{value!r}]"
                    case (False, False): return f"{name}: {param.annotation.__name__} = {type(value).__name__}[{value!r}]"
            
            fn_args: list[str] = []
            if pos_only_params:
                fn_args.append(", ".join(view_param(name) for name in pos_only_params))
                fn_args.append("/")
            if pos_or_kw_params:
                fn_args.append(", ".join(view_param(name) for name in pos_or_kw_params))
            if kw_only_params:
                fn_args.append(("*" + view_param(pos_var_param, var=True)) if pos_var_param else "*")
                fn_args.append(", ".join(view_param(name) for name in kw_only_params))
            if kw_var_param:
                fn_args.append("**" + view_param(kw_var_param, var=True))

            fn_arg_str: str = ", ".join(fn_args)

            output(f"Calling {type(func).__name__} {func.__name__}({fn_arg_str})")

            return_str: str = ""
            return_annotation: Any = fnc_sig.return_annotation
            if return_annotation is not inspect._empty:
                if return_annotation is not None:
                    return_str: str = f" -> {return_annotation.__name__}"
                else:
                    return_str: str = f" -> None"

            timer = datetime.datetime.now()

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                output(f"Exception in {type(func).__name__} {func.__name__}{return_str}: {e!r}")
                if not catch_exceptions:
                    raise
                return None
            
            timer = datetime.datetime.now() - timer
            output(f"Value returned by {type(func).__name__} {func.__name__}{return_str}: {type(result).__name__}[{result!r}]")
            output(f"Execution time for {type(func).__name__} {func.__name__}: {timer.total_seconds():.6f} seconds")

            return result
        return inner
    return wrapper
