from functools import wraps

from django.shortcuts import redirect

from .utils.verify import parse_config, model_exists

def verify(base_redir, *verifiers):
    
    def decorator(fn):
        
        @wraps(fn)
        def wrapper(request, *args, **kwargs):
            
            for config in verifiers:
                model, arg_name, redir = parse_config(config)
                
                return_val = model_exists(request, model, arg_name, kwargs)
                
                if return_val:
                    kwargs.update(return_val)
                elif redir:
                    return redirect(redir)
                else:
                    return redirect(base_redir)
            
            return fn(request, *args, **kwargs)
        
        return wrapper
    
    return decorator
