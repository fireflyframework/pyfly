"""BeanPostProcessor that wires declarative @http_client beans."""
from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any


class HttpClientBeanPostProcessor:
    """Replaces stub methods on @http_client beans with real HTTP calls.

    For each method with __pyfly_http_method__ metadata, generates an
    implementation that delegates to an HttpClientPort instance.
    """

    def __init__(
        self, http_client_factory: Callable[[str], Any] | None = None
    ) -> None:
        self._factory = http_client_factory or self._default_factory
        self._clients: dict[str, Any] = {}

    @staticmethod
    def _default_factory(base_url: str) -> Any:
        from pyfly.client.adapters.httpx_adapter import HttpxClientAdapter

        return HttpxClientAdapter(base_url=base_url)

    def before_init(self, bean: Any, bean_name: str) -> Any:
        return bean

    def after_init(self, bean: Any, bean_name: str) -> Any:
        cls = type(bean)
        if not getattr(cls, "__pyfly_http_client__", False):
            return bean

        base_url = getattr(cls, "__pyfly_http_base_url__", "")
        client = self._factory(base_url)
        self._clients[bean_name] = client

        for attr_name in dir(cls):
            attr = getattr(cls, attr_name, None)
            if attr is None:
                continue
            http_method = getattr(attr, "__pyfly_http_method__", None)
            if http_method is None:
                continue
            http_path = getattr(attr, "__pyfly_http_path__", "")
            impl = self._make_method_impl(client, http_method, http_path, attr)
            setattr(bean, attr_name, impl.__get__(bean, cls))

        return bean

    @staticmethod
    def _make_method_impl(
        client: Any, http_method: str, path_template: str, original: Any
    ) -> Any:
        sig = inspect.signature(original)

        async def implementation(self_arg: Any, *args: Any, **kwargs: Any) -> Any:
            bound = sig.bind(self_arg, *args, **kwargs)
            bound.apply_defaults()
            params = dict(bound.arguments)
            params.pop("self", None)

            # Resolve path variables
            path = path_template
            path_vars: set[str] = set()
            for key, value in params.items():
                placeholder = f"{{{key}}}"
                if placeholder in path:
                    path = path.replace(placeholder, str(value))
                    path_vars.add(key)

            remaining = {k: v for k, v in params.items() if k not in path_vars}

            request_kwargs: dict[str, Any] = {}
            if http_method in ("POST", "PUT", "PATCH") and "body" in remaining:
                request_kwargs["json"] = remaining.pop("body")
            if remaining:
                request_kwargs["params"] = remaining

            response = await client.request(http_method, path, **request_kwargs)
            return response.json()

        return implementation
