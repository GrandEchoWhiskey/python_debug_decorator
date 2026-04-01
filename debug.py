from typing import Callable, Any
from inspect import signature, Parameter

def debug(*, output: Callable[[str], None] = print, catch_exceptions: bool = False):
    """
    A debugging decorator that logs function calls with detailed parameter information.
    This decorator traces function execution by capturing and displaying:
    - All positional-only, positional-or-keyword, keyword-only arguments
    - Variable positional (*args) and keyword (**kwargs) parameters
    - Parameter types and values
    - Return values and exceptions
    Args:
        output: Callable to handle debug messages (default: print)
        catch_exceptions: If True, suppress exceptions and return None; if False, re-raise them
    Returns:
        A wrapper function that logs function invocation details before and after execution
    """
    def wrapper(func: Callable) -> Callable:

        PARAMS = signature(func).parameters
        POSITIONAL = {k: v for k, v in PARAMS.items() if v.kind == Parameter.POSITIONAL_ONLY}
        POSITIONAL_OR_KEYWORD = {k: v for k, v in PARAMS.items() if v.kind == Parameter.POSITIONAL_OR_KEYWORD}
        VAR_POSITIONAL = next((v for v in PARAMS.values() if v.kind == Parameter.VAR_POSITIONAL), None)
        KEYWORD = {k: v for k, v in PARAMS.items() if v.kind == Parameter.KEYWORD_ONLY}
        VAR_KEYWORD = next((v for v in PARAMS.values() if v.kind == Parameter.VAR_KEYWORD), None)

        def inner(*args, **kwargs):

            pos_only: dict[str, Any] = dict(zip(POSITIONAL.keys(), args[:len(POSITIONAL)]))
            pos_or_kw: dict[str, Any] = dict(zip(POSITIONAL_OR_KEYWORD.keys(), args[len(POSITIONAL):len(POSITIONAL) + len(POSITIONAL_OR_KEYWORD)]))
            var_pos: dict[str, list[Any]] = {VAR_POSITIONAL.name: list(args[len(POSITIONAL) + len(POSITIONAL_OR_KEYWORD):])} if VAR_POSITIONAL else {}
            kw_only: dict[str, Any] = {k: kwargs[k] for k in KEYWORD.keys() if k in kwargs}
            var_kw: dict[str, dict[str, Any]] = {VAR_KEYWORD.name: {k: v for k, v in kwargs.items() if k not in POSITIONAL_OR_KEYWORD and k not in KEYWORD}} if VAR_KEYWORD else {}

            list_of_pargs = [f"{k}: {PARAMS[k].annotation.__name__} = {type(v).__name__}[{v!r}]" for k, v in {**pos_only}.items()]
            list_of_args = [f"{k}: {PARAMS[k].annotation.__name__} = {type(v).__name__}[{v!r}]" for k, v in {**pos_or_kw}.items()]
            pos_var = f"*{VAR_POSITIONAL.name}: {VAR_POSITIONAL.annotation.__name__} = {type(var_pos[VAR_POSITIONAL.name]).__name__}[{', '.join(map(str, var_pos[VAR_POSITIONAL.name]))}]" if VAR_POSITIONAL else None
            list_of_kw = [f"{k}: {PARAMS[k].annotation.__name__} = {type(v).__name__}[{v!r}]" for k, v in kw_only.items()]
            kw_var = f"**{VAR_KEYWORD.name}: {VAR_KEYWORD.annotation.__name__} = {type(var_kw[VAR_KEYWORD.name]).__name__}[{', '.join(f'{k} = {type(v).__name__}[{v!r}]' for k, v in var_kw[VAR_KEYWORD.name].items())}]" if VAR_KEYWORD else None
            
            fn_args = ", ".join(filter(None, list_of_pargs + ['/',] + list_of_args + [pos_var] + list_of_kw + [kw_var]))

            output(f"Calling {type(func).__name__} {func.__name__}({fn_args})")

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                output(f"Exception in {type(func).__name__} {func.__name__}: {e!r}")
                if not catch_exceptions: raise
                return None

            output(f"Returned by {type(func).__name__} {func.__name__}: {type(result).__name__}[{result!r}]")

            return result
        return inner
    return wrapper
