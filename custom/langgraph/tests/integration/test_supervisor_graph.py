"""Integration tests for the supervisor graph end-to-end."""

from langchain_core.messages import HumanMessage

from src.graphs.supervisor import build_supervisor_graph
from src.models.pipeline import OutputStatus, TaskType


class TestSupervisorGraph:
    """Tests run the full supervisor → sub-agent pipeline (no LLM needed)."""

    def test_skill_creation_e2e(self):
        graph = build_supervisor_graph().compile()
        result = graph.invoke(
            {
                "messages": [
                    HumanMessage(content="Create a skill for debugging Python applications")
                ],
                "task_type": None,
                "current_phase": "",
                "model_profile": None,
                "pipeline_input": None,
                "pipeline_output": None,
                "completion_flags": {},
                "error_log": [],
                "routing_history": [],
            },
            config={"recursion_limit": 20},
        )

        output = result["pipeline_output"]
        assert output.task_type == TaskType.SKILL_CREATE
        assert output.output.status in (OutputStatus.SUCCESS, OutputStatus.PARTIAL)
        if output.output.status == OutputStatus.SUCCESS:
            assert len(output.output.files_created) > 0

    def test_agent_creation_e2e(self):
        graph = build_supervisor_graph().compile()
        result = graph.invoke(
            {
                "messages": [HumanMessage(content="Create an agent for data pipeline management")],
                "task_type": None,
                "current_phase": "",
                "model_profile": None,
                "pipeline_input": None,
                "pipeline_output": None,
                "completion_flags": {},
                "error_log": [],
                "routing_history": [],
            },
            config={"recursion_limit": 20},
        )

        output = result["pipeline_output"]
        assert output.task_type == TaskType.AGENT_CREATE
        assert output.output.status == OutputStatus.SUCCESS

    def test_steering_creation_e2e(self):
        graph = build_supervisor_graph().compile()
        result = graph.invoke(
            {
                "messages": [
                    HumanMessage(content="Write a steering doc for API naming conventions")
                ],
                "task_type": None,
                "current_phase": "",
                "model_profile": None,
                "pipeline_input": None,
                "pipeline_output": None,
                "completion_flags": {},
                "error_log": [],
                "routing_history": [],
            },
            config={"recursion_limit": 20},
        )

        output = result["pipeline_output"]
        assert output.task_type == TaskType.STEERING_WRITE
        assert output.output.status == OutputStatus.SUCCESS

    def test_tool_creation_e2e(self):
        graph = build_supervisor_graph().compile()
        result = graph.invoke(
            {
                "messages": [HumanMessage(content="Create a tool for querying Elasticsearch")],
                "task_type": None,
                "current_phase": "",
                "model_profile": None,
                "pipeline_input": None,
                "pipeline_output": None,
                "completion_flags": {},
                "error_log": [],
                "routing_history": [],
            },
            config={"recursion_limit": 20},
        )

        output = result["pipeline_output"]
        assert output.task_type == TaskType.TOOL_BUILD
        assert output.output.status == OutputStatus.SUCCESS

    def test_routing_history_populated(self):
        graph = build_supervisor_graph().compile()
        result = graph.invoke(
            {
                "messages": [HumanMessage(content="Create a skill for testing")],
                "task_type": None,
                "current_phase": "",
                "model_profile": None,
                "pipeline_input": None,
                "pipeline_output": None,
                "completion_flags": {},
                "error_log": [],
                "routing_history": [],
            },
            config={"recursion_limit": 20},
        )

        assert len(result["routing_history"]) > 0
