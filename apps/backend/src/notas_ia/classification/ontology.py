"""Ontologia pequena e estável compartilhada pelo benchmark e pelo backend."""

VIOLENCE_TYPES = ("fisica", "psicologica", "sexual", "patrimonial", "moral", "vicaria")
INTENTS = ("relato", "informacao", "ajuda_urgente", "atendimento_humano", "outro")
URGENCIES = ("imediata", "prioritaria", "sem_urgencia_detectada", "indeterminada")

TYPE_DESCRIPTIONS = {
    "fisica": "agressão, lesão, empurrão, tapa, estrangulamento ou ameaça física",
    "psicologica": "ameaça, humilhação, controle, isolamento, manipulação ou intimidação",
    "sexual": "ato ou contato sexual sem consentimento, coerção ou impedimento de contracepção",
    "patrimonial": "retenção, destruição, controle ou subtração de dinheiro, documentos ou bens",
    "moral": "calúnia, difamação, injúria ou exposição que atinge reputação e dignidade",
    "vicaria": "uso de filhos, familiares, animais ou pessoas próximas para causar sofrimento",
}

INTENT_DESCRIPTIONS = {
    "relato": "compartilhar ou narrar uma situação vivida ou observada",
    "informacao": "pedir explicação geral sobre direitos, violência ou serviços",
    "ajuda_urgente": "pedir ajuda diante de necessidade urgente ou possível perigo atual",
    "atendimento_humano": "pedir explicitamente uma pessoa, atendente ou serviço humano",
    "outro": "conteúdo fora do escopo, teste, ruído ou intenção não classificável acima",
}

URGENCY_DESCRIPTIONS = {
    "imediata": "há perigo atual ou iminente explicitamente relatado",
    "prioritaria": "há risco relevante, mas sem perigo atual ou iminente claramente estabelecido",
    "sem_urgencia_detectada": "não há sinal de urgência no material disponível",
    "indeterminada": "as informações são insuficientes, ambíguas ou contraditórias",
}
