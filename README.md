# Intelligent Project Development System

An AI-agent-based automated project development system that leverages collaborative AI agents with specialized roles to complete software development tasks.

## System Architecture

- **Product Manager Agent**: Responsible for generating the Product Requirements Document (PRD).  
- **Project Manager Agent**: Responsible for creating development guidelines and project plans.  
- **Frontend Developer Agent**: Responsible for developing and implementing the frontend application.  
- **Backend Developer Agent**: Responsible for developing and implementing the backend service.  
- **System Manager Agent**: Coordinates all agents and manages the overall project workflow.

## Technology Stack

- Python 3.10+  
- OpenAI LLM API  
- Custom AI Agent Factory Framework  
- Python-dotenv (environment variable management)

## Environment Configuration

1. Copy the `.env.example` file and rename it to `.env`.  
2. Configure the following environment variables in `.env`:

```bash
api_key=your_openai_api_key
model_name=your_model_name
base_url=your_base_url
```

## Running the System

```bash
python enhanced_main.py
```

## Usage Instructions

1. **Initial Stage**: Enter your project requirements — the system will automatically generate and develop the full project.  
2. **Post-Development**: Input updated requirements to modify and iterate on the existing project.  
3. **System Commands**:
   - `status` — View the current project status  
   - `next` — Execute the next development step  
   - `quit` — Exit the system

## Key Features

- Fully automated project development workflow  
- Multi-agent collaborative architecture  
- Intelligent state tracking and management  
- Support for iterative development and requirement changes  
- Built-in error handling and recovery mechanisms

## Project Status Tracking

The system automatically tracks the following development milestones:
- PRD (Product Requirements Document) completed  
- Development guidelines completed  
- Backend development completed  
- Frontend development completed

## Development Workflow

1. User submits project requirements.  
2. Product Manager Agent generates the PRD.  
3. Project Manager Agent creates detailed development guidelines.  
4. Frontend and Backend Developer Agents develop in parallel.  
5. System Manager Agent coordinates integration and ensures alignment.

## Notes

- An active OpenAI API key is required.  
- A stable internet connection is necessary to access LLM services.  
- The system automatically switches to modification mode once initial development is complete.

