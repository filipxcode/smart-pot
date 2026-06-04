from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch
from uuid import uuid4

from pydantic import BaseModel
from pydantic_ai.messages import ModelResponse
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext

import agent.tools.read_sensor as read_sensor_mod
import agent.tools.search_document as search_document_mod
import agent.tools.water_plant as water_plant_mod
from agent.deps import ChatDeps
from agent.retrieval.rag_search import ChunkHit
from agent.tool_agent import _tool_agent


# --- typy wejścia/wyjścia -------------------------------------------------

class ToolCall(BaseModel):
    """Pojedyncze wywołanie narzędzia zarejestrowane w przebiegu agenta."""

    name: str
    args: dict


class ExpectedTool(BaseModel):
    name: str
    args: dict = {}


class Expectation(BaseModel):
    tools: list[ExpectedTool]


async def run_tool_agent(query: str) -> list[ToolCall]:
    deps = ChatDeps(
        session=None,
        openai=None,
        user_id=uuid4(),
        device_id=1,
        embedding_model="text-embedding-3-small",
    )
    result = await _tool_agent.run(query, deps=deps)
    return [
        ToolCall(name=part.tool_name, args=part.args_as_dict())
        for msg in result.all_messages()
        if isinstance(msg, ModelResponse)
        for part in msg.tool_calls
    ]

def _value_matches(expected, actual) -> bool:
    if isinstance(expected, list):
        actual = actual or []
        return all(item in actual for item in expected)
    return str(actual) == str(expected) or str(actual).startswith(str(expected))


def _tool_args_match(exp: ExpectedTool, called: list[ToolCall]) -> bool:
    calls = [c for c in called if c.name == exp.name]
    if not calls:
        return False
    for key, expected_val in exp.args.items():
        if isinstance(expected_val, list):
            union = [item for c in calls for item in (c.args.get(key) or [])]
            if not all(item in union for item in expected_val):
                return False
        elif not any(_value_matches(expected_val, c.args.get(key)) for c in calls):
            return False
    return True


@dataclass
class ToolSelection(Evaluator[str, list[ToolCall]]):
    async def evaluate(
        self, ctx: EvaluatorContext[str, list[ToolCall]]
    ) -> dict[str, bool]:
        called = ctx.output
        expected = ctx.expected_output.tools

        names_ok = all(
            any(c.name == exp.name for c in called) for exp in expected
        )
        args_ok = all(_tool_args_match(exp, called) for exp in expected)
        return {"tools_called": names_ok, "args_match": args_ok}

dataset = Dataset[str, Expectation, None](
    name="tool_selection",
    cases=[
        # 1. jednorazowe podlanie z jawnym czasem
        Case(
            name="water_now_30s",
            inputs="podlej roślinę na 30 sekund",
            expected_output=Expectation(
                tools=[ExpectedTool(name="water_plant", args={"watering_time": 30})]
            ),
        ),
        # 2. odczyt parametrów (read_sensor zwraca zawsze komplet, bez argumentów)
        Case(
            name="read_root_temp",
            inputs="jaka jest temperatura korzeni?",
            expected_output=Expectation(
                tools=[ExpectedTool(name="read_sensor")]
            ),
        ),
        # 3. pytanie o kilka parametrów — wciąż jedno wywołanie read_sensor()
        Case(
            name="read_multi_sensor",
            inputs="sprawdź wilgotność gleby i natężenie światła",
            expected_output=Expectation(
                tools=[ExpectedTool(name="read_sensor")]
            ),
        ),
        # 4. harmonogram cykliczny w wybrane dni
        Case(
            name="schedule_specific_days",
            inputs="ustaw podlewanie w poniedziałki i czwartki o 8:00 na 20 sekund",
            expected_output=Expectation(
                tools=[
                    ExpectedTool(
                        name="schedule_watering_plant",
                        args={
                            "time_of_day": "08:00",
                            "days": ["mon", "thu"],
                            "duration_sec": 20,
                        },
                    )
                ]
            ),
        ),
        # 5. harmonogram codzienny (brak listy dni)
        Case(
            name="schedule_daily",
            inputs="podlewaj roślinę codziennie rano o 7",
            expected_output=Expectation(
                tools=[
                    ExpectedTool(
                        name="schedule_watering_plant",
                        args={"time_of_day": "07:00"},
                    )
                ]
            ),
        ),
        # 6. pytanie o wiedzę z dokumentów → search_document
        Case(
            name="doc_lookup",
            inputs="co w moich dokumentach pisze o podlewaniu storczyka?",
            expected_output=Expectation(
                tools=[ExpectedTool(name="search_document")]
            ),
        ),
        # 7. DEKOMPOZYCJA: odczyt, a potem akcja (dwa narzędzia)
        Case(
            name="decompose_read_then_water",
            inputs="sprawdź temperaturę powietrza, a potem podlej roślinę na 15 sekund",
            expected_output=Expectation(
                tools=[
                    ExpectedTool(name="read_sensor"),
                    ExpectedTool(name="water_plant", args={"watering_time": 15}),
                ]
            ),
        ),
        # 8. DEKOMPOZYCJA: odczyt + wiedza z dokumentów (read + RAG)
        Case(
            name="decompose_read_then_doc",
            inputs="sprawdź wilgotność powietrza i powiedz, co moje notatki mówią o idealnej wilgotności",
            expected_output=Expectation(
                tools=[
                    ExpectedTool(name="read_sensor"),
                    ExpectedTool(name="search_document"),
                ]
            ),
        ),
    ],
    evaluators=[ToolSelection()],
)

async def _fake_hybrid_search(*args, **kwargs) -> list[ChunkHit]:
    return [
        ChunkHit(
            chunk_id=1,
            document_id=1,
            chunk_text="Podlewaj umiarkowanie, gdy wierzchnia warstwa podłoża przeschnie.",
            document_title="Notatki o roślinach",
            similarity=0.9,
            cosine_similarity=0.85,
        )
    ]


async def _fake_read_sensor_service(*args, **kwargs) -> dict[str, float | None]:
    return {
        "air_temp": 22.5,
        "air_hum": 55.0,
        "root_temp": 20.0,
        "soil_hum": 40.0,
        "light_lux": 800.0,
    }


async def _fake_water_plant_service(*args, **kwargs) -> bool:
    return True


if __name__ == "__main__":
    with (
        patch.object(search_document_mod, "hybrid_search", _fake_hybrid_search),
        patch.object(read_sensor_mod, "read_sensor_service", _fake_read_sensor_service),
        patch.object(water_plant_mod, "water_plant_service", _fake_water_plant_service),
    ):
        report = dataset.evaluate_sync(run_tool_agent)
    report.print(include_input=True, include_output=True)
