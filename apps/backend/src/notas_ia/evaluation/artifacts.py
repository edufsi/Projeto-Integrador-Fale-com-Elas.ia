from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_jsonl(path: Path, value: Any) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False) + "\n")


def audit_payload(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "evaluation-human-audit.v1",
        "instruction": "Edite apenas auditoria_humana; mantenha a saída do sistema intacta.",
        "items": [{
            "record_id": item["record_id"], "review_status": item["review_status"],
            "history": item["history"], "message": item["message"], "expected": item["expected"],
            "response": item.get("response", {}), "response_rubric": item.get("response_rubric", {}),
            "observed_action": item.get("observed_action"),
            "auditoria_humana": {"status": "pendente", "obrigacoes_cumpridas": [],
                                  "proibicoes_violadas": [], "orientacao_perigosa": None,
                                  "comentario": ""},
        } for item in records],
    }


def preserve_human_audit(audit: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    """Copy only human-review fields from an earlier audit export.

    The recorded system response is intentionally rebuilt from `records.jsonl` so
    it cannot be edited accidentally, while a reviewer can refresh the HTML without
    losing their annotations.
    """
    existing = {
        item.get("record_id"): item.get("auditoria_humana")
        for item in (previous or {}).get("items", [])
        if isinstance(item, dict) and isinstance(item.get("auditoria_humana"), dict)
    }
    for item in audit["items"]:
        human = existing.get(item["record_id"])
        if human is not None:
            item["auditoria_humana"] = human
    return audit


def render_markdown(report: dict[str, Any], manifest: dict[str, Any]) -> str:
    lines = ["# Relatório de avaliação", "", f"- Execução: `{manifest['run_id']}`", f"- Preset: `{manifest['preset']}`", ""]
    for status, data in report["by_review_status"].items():
        lines += [f"## {status}", "", f"Turnos: {data['turns']}"]
        for profile, metric in data["classification"].items():
            lines.append(f"- `{profile}`: cobertura {metric.get('coverage', 0)}, tipos exatos {metric.get('types_exact')}, intenção {metric.get('intent_accuracy')}, urgência {metric.get('urgency_accuracy')}, recall imediata {metric.get('immediate', {}).get('recall')}")
        lines.append(f"- Ações observadas: {data['agent']['observed_actions']}")
        lines.append(
            f"- Falhas de ferramenta: {data['agent']['tool_failures']}; "
            f"respostas com fonte: {data['agent']['responses_with_sources']}; "
            f"fontes devolvidas: {data['agent']['sources_returned']}; "
            f"fallback de citação: {data['agent']['citation_fallbacks']}; "
            f"fallback de canais: {data['agent']['controlled_resource_fallbacks']}"
        )
        lines.append("")
    if report["blocked_suites"]:
        lines += ["## Suites bloqueadas", ""]
        lines += [f"- `{item['suite']}`: {item['reason']}" for item in report["blocked_suites"]]
    return "\n".join(lines) + "\n"


def render_comparison_markdown(comparison: dict[str, Any]) -> str:
    """Render a compact, status-preserving view of comparable evaluation runs.

    A comparison intentionally does not collapse review statuses into one score: a
    result from a singly reviewed exploratory suite cannot become an alleged gold
    result merely because it is displayed beside a draft corpus.
    """
    lines = [
        "# Comparação de rodadas",
        "",
        f"- Hash do corpus: `{comparison['dataset_fingerprint']}`",
        "- Métricas só devem ser comparadas dentro da mesma seção de status.",
        "",
    ]
    statuses = sorted({
        status for run in comparison["runs"]
        for status in run["by_review_status"]
    })
    for status in statuses:
        lines.extend([f"## {status}", "", "| Rodada | Turnos | Classificador | Tipos exatos | Intenção | Urgência | Recall imediata | Latência p50 (ms) |", "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |"])
        for run in comparison["runs"]:
            data = run["by_review_status"].get(status)
            if not data:
                continue
            classifiers = data.get("classification", {})
            if classifiers:
                profile, classification = next(iter(classifiers.items()))
                exact = classification.get("types_exact")
                intent = classification.get("intent_accuracy")
                urgency = classification.get("urgency_accuracy")
                immediate = classification.get("immediate", {}).get("recall")
            else:
                profile, exact, intent, urgency, immediate = "—", "—", "—", "—", "—"
            p50 = data.get("performance", {}).get("round_trip_ms", {}).get("median")
            lines.append(
                f"| `{run['preset']}` | {data.get('turns', 0)} | `{profile}` | "
                f"{exact} | {intent} | {urgency} | {immediate} | {p50} |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def render_html(audit: dict[str, Any], title: str) -> str:
    payload = json.dumps(audit, ensure_ascii=False).replace("</", "<\\/")
    safe_title = html.escape(title)
    return f"""<!doctype html><html lang=\"pt-BR\"><meta charset=\"utf-8\"><title>{safe_title}</title>
<style>body{{font:15px system-ui;max-width:1100px;margin:2rem auto;padding:0 1rem}}article{{border:1px solid #ccc;padding:1rem;margin:1rem 0}}pre{{white-space:pre-wrap;background:#f6f6f6;padding:.75rem}}select{{padding:.4rem}}</style>
<h1>{safe_title}</h1><p>Relatório estático: edite <code>audit.json</code> para registrar revisão humana.</p>
<label>Status <select id=\"status\"><option value=\"\">todos</option></select></label><main id=\"items\"></main>
<script>const data={payload};const sel=document.querySelector('#status'),main=document.querySelector('#items');
for(const s of [...new Set(data.items.map(x=>x.review_status))])sel.add(new Option(s,s));
function draw(){{main.innerHTML='';for(const x of data.items){{if(sel.value&&x.review_status!==sel.value)continue;const r=x.response.assistant_message?.content||'(falha)';main.insertAdjacentHTML('beforeend',`<article><b>${{x.record_id}}</b> — ${{x.review_status}}<h3>Histórico</h3><pre>${{[...x.history,x.message].join('\\n')}}</pre><h3>Resposta</h3><pre>${{r}}</pre><h3>Esperado</h3><pre>${{JSON.stringify(x.expected,null,2)}}</pre><h3>Observado</h3><pre>${{JSON.stringify({{acao:x.observed_action,classificacoes:x.response.classifications,ferramentas:x.response.agent}},null,2)}}</pre></article>`);}}}}sel.onchange=draw;draw();</script>"""
