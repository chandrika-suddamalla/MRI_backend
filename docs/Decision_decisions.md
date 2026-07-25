## Design Decisions

The backend was designed to provide a clean, modular, and production-oriented architecture while remaining lightweight and aligned with the scope of the assignment. The design emphasises maintainability, scalability, and clear separation of responsibilities.

### Modular Architecture

The application is organised into independent modules, including:

- Authentication
- API Routing
- AI Services
- Data Models
- Utilities
- Infrastructure

This modular approach provides several benefits:

- **Maintainability:** Each module has a single responsibility, making the codebase easier to understand and modify.
- **Testability:** Individual components can be tested independently, improving code quality and simplifying debugging.
- **Readability:** A clear project structure makes it easier for developers to navigate and contribute to the codebase.
- **Extensibility:** New features, AI models, or research pipelines can be integrated with minimal changes to the existing architecture.

This design enables the application to evolve while keeping the codebase organised and maintainable.

---

## FastAPI

FastAPI was selected because it provides:

- High performance
- Native asynchronous support
- Automatic request validation using Pydantic
- Interactive API documentation
- Excellent developer productivity

These characteristics make it well suited for AI-powered backend services.

---

## Google Gemini

Google Gemini was selected as the primary Large Language Model because it provides:

- High-quality summarisation
- Strong reasoning capabilities
- Structured output generation
- Reliable handling of long contextual inputs
- Developer-friendly API integration

The model is responsible for transforming raw research data into actionable market intelligence.

---

## LLM-as-a-Judge

A second AI evaluation stage was introduced to improve trust in generated outputs.

Rather than returning the initial LLM response directly, the generated report is independently evaluated for:

- Factual consistency
- Source grounding
- Unsupported claims
- Hallucinations
- Overall confidence

This additional validation layer increases transparency and reliability.

---

## Infrastructure as Code

Terraform is used to provision cloud resources instead of manual deployment.

Benefits include:

- Repeatable deployments
- Version-controlled infrastructure
- Reduced configuration drift
- Easier collaboration
- Simplified environment recreation

---

## Docker

Containerisation ensures that the application runs consistently across different environments.

Benefits include:

- Reproducible builds
- Simplified deployment
- Environment consistency
- Easier cloud hosting

---

# Engineering Trade-offs

Every engineering solution involves trade-offs. The following decisions were intentionally made based on the assignment scope.

| Decision | Trade-off |
|-----------|-----------|
| Synchronous report generation | Simpler implementation with immediate user feedback; long-running jobs could later be moved to a background queue. |
| Single LLM provider | Reduced implementation complexity while keeping the architecture extensible for additional providers. |
| Basic report persistence | Sufficient for assignment requirements; future versions could include richer search and analytics. |
| JWT authentication | Lightweight and stateless, avoiding the overhead of server-side session management. |
| Immediate scraping | Fresh data for each request at the expense of longer response times compared to cached content. |

---

# Reliability Considerations

The application has been designed to handle common failure scenarios gracefully.

Examples include:

- Invalid or malformed URLs
- Missing required fields
- Authentication failures
- Expired access tokens
- AI service errors
- Network timeouts
- Unexpected server exceptions

Where appropriate, meaningful HTTP status codes and descriptive error messages are returned instead of exposing internal implementation details.

---

# Scalability Considerations

Although the assignment targets a lightweight implementation, the architecture has been designed with future scalability in mind.

Potential enhancements include:

- Background task processing using message queues
- Distributed caching for frequently analysed sources
- Support for multiple LLM providers
- Vector databases for semantic search
- Incremental "What's New" market monitoring
- Scheduled research jobs
- Horizontal scaling through container orchestration

---

# Future Enhancements

The following improvements could further extend the application:

- Change detection between previous and current reports
- Scheduled market monitoring
- Email notifications for new competitor activity
- Multi-language research support
- Semantic search using vector embeddings
- Dashboard with historical trends
- User-configurable prompt templates
- Additional LLM provider integrations
- Confidence scoring for generated insights
- Streaming AI responses for improved user experience

---

# AI Tools, Models & References

The following AI technologies and development tools were used during the implementation of this project.

## AI Model

- **Google Gemini** – Primary Large Language Model used for market intelligence generation and structured summarisation.

## AI Validation

- **LLM-as-a-Judge** – Used to evaluate generated reports for factual consistency and hallucination detection.

## Libraries

- FastAPI
- Pydantic
- Requests
- BeautifulSoup
- PyJWT
- Python standard cryptographic libraries
- Terraform
- Docker

## Development Assistance

Generative AI tools were used during development to assist with:

- Exploring implementation approaches
- Code refinement
- Documentation drafting
- Troubleshooting
- General productivity

All generated code and documentation were reviewed, validated, and modified as necessary before inclusion in the final submission.

---

# Conclusion

The **Market Research Intelligence Assistant** demonstrates the application of modern backend engineering practices to solve a real-world market intelligence problem using Generative AI.

The solution combines:

- Secure authentication
- Modular API design
- Automated web content processing
- AI-powered summarisation
- Hallucination verification using LLM-as-a-Judge
- Cloud-ready deployment with Docker and Terraform

The resulting system provides structured, source-grounded market intelligence while remaining maintainable, extensible, and suitable for future enhancements.

---