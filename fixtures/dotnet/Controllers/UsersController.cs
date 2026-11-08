using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Authorization;

namespace SampleApp.Controllers
{
    [ApiController]
    [Route("api/v1/[controller]")]
    public class UsersController : ControllerBase
    {
        [HttpGet]
        public IActionResult GetAll()
        {
            return Ok(new[] { new { id = 1, name = "Alice" } });
        }

        [HttpGet("{id}")]
        public IActionResult GetById(int id)
        {
            return Ok(new { id = id, name = "Alice" });
        }

        [HttpPost]
        [Authorize]
        public IActionResult Create([FromBody] object payload)
        {
            return CreatedAtAction(nameof(GetById), new { id = 2 }, payload);
        }
    }
}

