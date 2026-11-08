# Reference: Layered API Discovery Protocol

This document details the inspection checklist across the 6 discovery layers for ASP.NET Core, FastAPI, and Express.js.

## 1. ASP.NET Core (.NET)
- **Layer 1**: Look for `Swashbuckle.AspNetCore` / `NSwag` configurations in `Program.cs` or generated `swagger.json`.
- **Layer 2**:
  - Controllers: Classes inheriting from `ControllerBase` or `Controller` with `[ApiController]` and `[Route("...")]`.
  - Minimal APIs: `app.MapGet()`, `app.MapPost()`, `app.MapGroup("/prefix")`.
- **Layer 3**: Attribute inspection `[HttpGet]`, `[HttpPost]`, `[Authorize]`, `[ProducesResponseType]`. Parameter binding attributes: `[FromBody]`, `[FromQuery]`, `[FromRoute]`, `[FromHeader]`.
- **Layer 4**: Extension methods registering endpoints (e.g. `endpoints.MapHub<ChatHub>()`).
- **Layer 5**: ASP.NET Core route endpoint data sources via `EndpointDataSource`.
- **Layer 6**: `Ocelot`, `YARP` (Yet Another Reverse Proxy), or IIS `web.config` rewrite rules.

## 2. FastAPI (Python)
- **Layer 1**: Automatic OpenAPI doc metadata: inspect `FastAPI(docs_url="/docs", openapi_url="/openapi.json")`.
- **Layer 2**: Decorators: `@app.get()`, `@router.post()`, `@router.delete()`. Router inclusion: `app.include_router(prefix="/api/v1", tags=["..."])`.
- **Layer 3**: Type annotations and Pydantic models: `Body(...)`, `Query(...)`, `Path(...)`, `Header(...)`, `Depends(...)`.
- **Layer 4**: FastAPI plugin mounts, starlette route extensions.
- **Layer 5**: Introspecting `app.routes` at runtime if non-side-effecting.
- **Layer 6**: Traefik, Nginx, or Docker Compose routing labels.

## 3. Express.js (Node / TypeScript)
- **Layer 1**: `swagger-ui-express`, `tsoa`, or OpenAPI yaml files.
- **Layer 2**: `app.use('/prefix', router)`, `router.get('/path', handler)`, `app.all()`.
- **Layer 3**: Route chains `router.route('/items').get().post()`. Middleware mounts for auth: `passport.authenticate()`, `jwtVerify()`.
- **Layer 4**: npm modules mounting express sub-apps.
- **Layer 5**: Introspecting `app._router.stack`.
- **Layer 6**: Nginx proxy pass, AWS API Gateway, Express Gateway configs.

