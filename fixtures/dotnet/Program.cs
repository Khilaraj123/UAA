// Sample ASP.NET Core Minimal API fixture for UAA testing
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.Hosting;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/health", () => Results.Ok(new { status = "healthy" }));
app.MapGet("/api/v1/products", () => Results.Ok(new[] { new { id = 1, name = "Laptop" } }));
app.MapPost("/api/v1/products", () => Results.Created("/api/v1/products/1", new { id = 1 }))
   .RequireAuthorization();

app.Run();

