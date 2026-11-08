# Reference: Deep Code Tracing Patterns

This guide outlines code patterns to trace when extracting endpoint behavior.

## 1. Authentication & Authorization Patterns
- **FastAPI**: Look for `Depends(get_current_user)`, `Security(scopes=[...])`, `HTTPBearer()`, `OAuth2PasswordBearer()`.
- **ASP.NET Core**: Look for `[Authorize]`, `[Authorize(Policy = "...")]`, `HttpContext.User.Claims`, `IAuthorizationService.AuthorizeAsync()`.
- **Express**: Look for `router.use(verifyToken)`, `passport.authenticate('jwt')`, `req.user`, `checkPermission('read:users')`.

## 2. Input Validation Patterns
- **Pydantic (Python)**: Field validators `@validator`, `conint(gt=0)`, `constr(min_length=1)`, `Config.extra = "forbid"`.
- **FluentValidation / DataAnnotations (.NET)**: `[Required]`, `[MaxLength(50)]`, `[RegularExpression(...)]`, `AbstractValidator<T>`.
- **Joi / Zod (Node.js)**: `z.object({...}).strict()`, `Joi.string().email().required()`.

## 3. Side-Effect & Downstream Calls
- Identify external HTTP clients: `requests`, `httpx`, `aiohttp`, `HttpClient`, `axios`, `fetch`.
- Trace database transactions: `session.commit()`, `_context.SaveChangesAsync()`, `knex('users').insert()`, `prisma.user.create()`.
- Flag risky operations: calls sending emails (`sendgrid`, `smtp`), charging cards (`stripe`), dispatching cloud events (`sqs`, `sns`, `kafka`).

