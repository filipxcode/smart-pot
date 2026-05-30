from __future__ import annotations

from dataclasses import dataclass

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge

from agent.prompts.prompts import PromptsOrganizer
from agent.rag_agent import _rag_agent

LOVE_THE_GARDEN = "Przewodnik po roślinach domowych w pigułce"
MODR = "Pielęgnacja roślin pokojowych"


@dataclass
class RAGInput:
    question: str
    context: str


async def run_rag_agent(inputs: RAGInput) -> str:
    user_message = PromptsOrganizer.rag_user(context=inputs.context, query=inputs.question)
    result = await _rag_agent.run(user_message)
    return result.output

GROUNDED = LLMJudge(
    rubric=(
        "Odpowiedź opiera się wyłącznie na informacjach z podanego kontekstu "
        "i nie dodaje faktów spoza niego."
    ),
    include_input=True,
    assertion={"evaluation_name": "grounded", "include_reason": True},
)

CITES = LLMJudge(
    rubric="Odpowiedź cytuje tytuł dokumentu źródłowego w nawiasach kwadratowych [tytuł].",
    include_input=True,
    assertion={"evaluation_name": "uses_citations", "include_reason": True},
)

REFUSES = LLMJudge(
    rubric=(
        "Odpowiedź przyznaje, że w kontekście nie ma odpowiedzi (np. 'Nie wiem'), "
        "zamiast zmyślać fakty."
    ),
    include_input=True,
    assertion={"evaluation_name": "admits_unknown", "include_reason": True},
)


dataset = Dataset[RAGInput, str, None](
    name="rag_evaluation",
    cases=[
        # --- Love the Garden -------------------------------------------------
        Case(
            name="temperatura_pokojowa",
            inputs=RAGInput(
                question="W jakim zakresie temperatur najlepiej trzymać rośliny domowe?",
                context=(
                    f"[1] {LOVE_THE_GARDEN}\n"
                    "Miejsca, w których światło jest dobre, temperatura waha się między "
                    "18°C - 24°C i jest dobra cyrkulacja powietrza, okażą się najlepszym "
                    "miejscem dla roślin domowych. Większość roślin woli temperatury pokojowe, "
                    "które są ciepłe w ciągu dnia i nieco chłodniejsze w nocy."
                ),
            ),
            evaluators=[CITES],
        ),
        Case(
            name="kiedy_podlewac",
            inputs=RAGInput(
                question="Po czym poznać, że roślinę doniczkową trzeba podlać?",
                context=(
                    f"[1] {LOVE_THE_GARDEN}\n"
                    "Zasadniczo należy podlewać tylko wtedy, gdy górne 5 cm podłoża wydają się "
                    "suche. Doskonałym sposobem sprawdzenia jest „test palca”: wystarczy włożyć "
                    "palec w podłoże aż do drugiej kostki. Jeśli ziemia wydaje się sucha, roślina "
                    "wymaga podlewania."
                ),
            ),
            evaluators=[CITES],
        ),
        Case(
            name="przesadzanie_storczyka",
            inputs=RAGInput(
                question="Jak często należy przesadzać storczyki?",
                context=(
                    f"[1] {LOVE_THE_GARDEN}\n"
                    "Przesadzaj rośliny tylko wtedy, gdy korzenie mniej więcej wypełniają "
                    "doniczkę. Rośliny domowe najlepiej przesadzać od marca do lipca. "
                    "Storczyki wymagają przesadzania co cztery do pięciu lat."
                ),
            ),
            evaluators=[CITES],
        ),
        Case(
            name="przedziorek_profilaktyka",
            inputs=RAGInput(
                question="Jak ograniczyć ryzyko pojawienia się przędziorków?",
                context=(
                    f"[1] {LOVE_THE_GARDEN}\n"
                    "Przędziorki to małe roztocza koloru pomarańczowego lub brązowego. "
                    "Preferują gorące, suche warunki i nie lubią dużej wilgotności, dlatego "
                    "należy codziennie zraszać rośliny."
                ),
            ),
            evaluators=[CITES],
        ),
        # --- MODR ------------------------------------------------------------
        Case(
            name="rozmiar_nowej_doniczki",
            inputs=RAGInput(
                question="O ile większą doniczkę dobrać przy przesadzaniu rośliny?",
                context=(
                    f"[2] {MODR}\n"
                    "Młode rośliny przesadzamy co roku, a starsze - zwłaszcza duże - co 3-4 lata. "
                    "Najodpowiedniejszą porą jest wczesna wiosna, koniec lutego, początek marca. "
                    "Przygotowujemy doniczki mniej więcej o średnicy 2 cm większe oraz świeże podłoże."
                ),
            ),
            evaluators=[CITES],
        ),
        Case(
            name="nawozenie_po_przesadzeniu",
            inputs=RAGInput(
                question="Kiedy można zacząć nawozić roślinę po przesadzeniu?",
                context=(
                    f"[2] {MODR}\n"
                    "Na dno nowej doniczki układamy drenaż, umieszczamy centralnie roślinę i "
                    "dosypujemy podłoża. Pamiętajmy, że po przesadzeniu odczekujemy miesiąc z "
                    "nawożeniem."
                ),
            ),
            evaluators=[CITES],
        ),
        Case(
            name="dlugosc_dnia_swietlnego",
            inputs=RAGInput(
                question="Ile godzin światła dziennie potrzebuje większość roślin pokojowych?",
                context=(
                    f"[2] {MODR}\n"
                    "Większość roślin potrzebuje od 12 do 16 godzin światła dziennego do "
                    "aktywnego rozwoju. Rośliny kwitnące potrzebują więcej światła niż rośliny "
                    "liściaste."
                ),
            ),
            evaluators=[CITES],
        ),
        Case(
            name="rodzaj_wody",
            inputs=RAGInput(
                question="Jakiej wody używać do podlewania roślin pokojowych?",
                context=(
                    f"[2] {MODR}\n"
                    "Zawsze lepiej podlać wodą letnią, albo przynajmniej o temperaturze pokojowej. "
                    "Zaleca się zostawić polewaczkę z wodą na noc w tym samym pomieszczeniu co "
                    "roślina, aby woda osiągnęła temperaturę pokojową i aby ulotniło się nieco chloru. "
                    "Nie wolno używać wody zmiękczanej chemikaliami."
                ),
            ),
            evaluators=[CITES],
        ),
        # --- negatywny: odpowiedzi nie ma w kontekście -----------------------
        Case(
            name="brak_w_kontekscie",
            inputs=RAGInput(
                question="Czy liście tej rośliny są trujące dla kota?",
                context=(
                    f"[1] {LOVE_THE_GARDEN}\n"
                    "Zasadniczo należy podlewać tylko wtedy, gdy górne 5 cm podłoża wydają się "
                    "suche. Użyj wody o temperaturze pokojowej, aby uniknąć zimnego szoku korzeni."
                ),
            ),
            evaluators=[REFUSES],
        ),
    ],
    evaluators=[GROUNDED],
)


if __name__ == "__main__":
    report = dataset.evaluate_sync(run_rag_agent)
    report.print(include_input=True, include_output=True)
