# Spike: Como obter a localização da usuária em uma aplicação web (React + Nest/Express)

## 1. Objetivo e escopo

Este documento investiga **como obter a localização da usuária** em uma
aplicação web com front-end em **React + TypeScript** e back-end em
**Node (NestJS ou Express)**, e **o que fazer com ela** no contexto do
chatbot de acolhimento (ver `arquitetura_chatbot_violencia_genero_IA.md`).

O uso mais provável da localização é **indicar serviços da rede de
atendimento próximos** (delegacia da mulher, centro de referência,
casa-abrigo, defensoria). Ela **não** é necessária para classificar
intenção, tipo de violência ou gravidade.

Perguntas que o spike responde:

1.  Quais são as formas de obter a localização e qual a precisão de cada
    uma?
2.  Qual combinação faz sentido para este projeto?
3.  Como implementar no front (React) e no back (Nest ou Express)?
4.  Quais os riscos de privacidade e de segurança da usuária?

**Restrição de projeto:** todas as soluções consideradas devem ser
**gratuitas e, preferencialmente, open source**. Serviços pagos ou
proprietários (Google Maps, Mapbox, ipinfo etc.) foram descartados. Para
cada necessidade há **mais de uma opção** (seção 2.1).

Fora do escopo: despacho automático de ajuda, rastreamento contínuo,
integração com serviços de emergência.

> **Nota:** limites de uso, licenças e políticas de serviços de terceiros
> citados abaixo mudam com o tempo. Os itens marcados com **(verificar)**
> devem ser conferidos na documentação oficial antes de entrarem no
> trabalho.

------------------------------------------------------------------------

## 2. Resumo da recomendação

``` text
1. Localização é PEDIDA SOB DEMANDA, por ação explícita da usuária
   ("Encontrar serviços perto de mim"), nunca ao abrir a página.
2. Fonte principal: Geolocation API do navegador (GPS/Wi-Fi).
3. Alternativa sempre disponível: informar CEP ou cidade/bairro.
4. Localização por IP (back-end): apenas como sugestão grosseira
   (cidade/UF) a ser confirmada, nunca como dado definitivo.
5. Preferir que a localização NÃO saia do dispositivo: baixar a lista de
   serviços e calcular a distância no navegador. Se for para o servidor,
   enviar coordenadas arredondadas, por POST, sem registrar em log.
6. Rota de emergência NÃO depende de localização.
```

O ponto 5 é a decisão de projeto mais importante: para esta aplicação, a
**melhor localização é a que o servidor nunca recebe**.

### 2.1 Opções gratuitas / open source por necessidade

  Necessidade                  Opção 1                              Opção 2                                   Opção 3
  ---------------------------- ------------------------------------ ----------------------------------------- ------------------------------------
  Posição do dispositivo       Geolocation API (padrão web, nativa) Cidade/UF escolhida em lista (IBGE)       CEP informado
  Localização por IP           DB-IP Lite (`.mmdb`, CC BY 4.0)      MaxMind GeoLite2 (gratuita, licença própria, **não** é open source) IP2Location LITE (gratuita, licença própria)
  Consulta de CEP              BrasilAPI (código aberto)            ViaCEP (gratuita)                         Tabela local de CEP → município
  Município a partir de coordenadas  *Point-in-polygon* com malhas do IBGE + Turf.js (MIT)  Nominatim próprio (reverse)  Nominatim público (uso leve)
  Geocodificação de endereço   Nominatim (OSM, software livre)      Photon (software livre, sobre dados OSM)  Pelias (software livre)
  Distância / busca de serviços  Haversine no navegador (sem banco) PostgreSQL + PostGIS                      Haversine em memória no Node
  Mapa (se for usado)          Leaflet (BSD) + tiles OSM            Leaflet + tiles hospedados por você       MapLibre GL JS + tiles próprios

As licenças, os limites de uso e a necessidade de atribuição de cada item
devem ser conferidos **(verificar)**. Itens "gratuitos, mas não open
source" são aceitáveis só se não houver alternativa livre equivalente; a
**opção 1 de cada linha** é a preferida por ser livre e por não enviar
dados da usuária a terceiros.

------------------------------------------------------------------------

## 3. Fontes de localização: comparação

  Fonte                            Precisão típica              Onde roda       Consentimento do navegador   Observações
  -------------------------------- ---------------------------- --------------- ---------------------------- ---------------------------------------------
  **Geolocation API** (GPS / Wi-Fi) metros a dezenas de metros (celular); centenas de metros a km (desktop) Front            Sim (prompt)                 Exige HTTPS; a usuária pode negar
  **IP** (base local ou API)       cidade ou região; pode errar a cidade Back-end        Não                          Ruim em rede móvel e com VPN
  **CEP informado**                rua/bairro                   Front → API     Não (ação manual)            Depende de base de CEP com coordenadas
  **Cidade/bairro digitados**      bairro/cidade                Front → API     Não                          Exige geocodificação
  **Dito no chat** ("moro em X")   variável                     Back-end (NER)  Não                          Complemento; exige extração de entidades

Conclusão da tabela: **nenhuma fonte é suficiente sozinha**. A Geolocation
API é a mais precisa, mas pode ser negada ou indisponível; as demais
funcionam como alternativas.

------------------------------------------------------------------------

## 4. Geolocation API do navegador

### 4.1 Como funciona

``` ts
navigator.geolocation.getCurrentPosition(sucesso, erro, opcoes);
```

-   Retorna `coords.latitude`, `coords.longitude` e `coords.accuracy`
    (raio de incerteza em metros).
-   O navegador mostra um **prompt de permissão**; o código não consegue
    forçar nem ocultar isso.
-   Só funciona em **contexto seguro** (HTTPS; `localhost` também vale
    em desenvolvimento).
-   O navegador combina GPS, Wi-Fi, torres de celular e IP. Em
    computadores sem GPS, a precisão é bem pior.

### 4.2 Erros possíveis

  Código                     Significado                     Tratamento sugerido
  -------------------------- ------------------------------- ------------------------------------------
  `1` PERMISSION_DENIED      Usuária negou (ou já estava bloqueado)  Oferecer CEP/cidade; não insistir
  `2` POSITION_UNAVAILABLE   Sem sinal, serviço desligado    Oferecer CEP/cidade
  `3` TIMEOUT                Demorou mais que o `timeout`    Permitir tentar de novo; oferecer CEP/cidade

### 4.3 Opções

``` ts
{
  enableHighAccuracy: false, // basta precisão de bairro; poupa bateria e é mais rápido
  timeout: 10_000,           // 10 s
  maximumAge: 5 * 60_000     // aceita posição em cache de até 5 min
}
```

Para listar serviços próximos **não é necessária alta precisão**.
`enableHighAccuracy: false` costuma responder mais rápido e funcionar
dentro de casa.

### 4.4 Usar `getCurrentPosition`, não `watchPosition`

`watchPosition` acompanha o movimento continuamente. Isso é rastreamento
e **não deve ser usado** neste projeto.

### 4.5 Comportamentos que merecem teste

-   **Negação é difícil de reverter:** depois de bloqueada, a página não
    consegue pedir de novo; a usuária precisa mudar a configuração do
    site no navegador. A interface deve explicar isso em linguagem
    simples e oferecer a alternativa manual.
-   **Navegadores embutidos** (webviews de redes sociais/mensageiros)
    podem não oferecer geolocalização ou ocultar o prompt.
-   **iOS/Safari** pode pedir permissão com mais frequência do que
    outros navegadores **(verificar)**.
-   Em **desktop**, `accuracy` pode ser de vários quilômetros: usar o
    campo para decidir se o resultado é confiável.
-   A API `navigator.permissions.query({ name: 'geolocation' })` permite
    saber se o estado é `granted`, `denied` ou `prompt` **sem disparar o
    prompt**, útil para ajustar a interface. Seu suporte varia **(verificar)**.
-   O cabeçalho `Permissions-Policy: geolocation=(self)` impede que
    scripts de terceiros embutidos peçam localização.

------------------------------------------------------------------------

## 5. Localização por IP (back-end)

### 5.1 Quando faz sentido

Só como **pré-seleção grosseira** de cidade/UF (ex.: "Você está em Porto
Alegre, RS?") quando a usuária ainda não informou nada. **Não** deve
alimentar uma recomendação de endereço específico.

### 5.2 Opções

  Opção                              Custo / licença                       Observações
  ---------------------------------- ------------------------------------- --------------------------------------
  **DB-IP Lite** (base local)        Gratuita, CC BY 4.0 (exige atribuição) Disponível em `.mmdb`, lido pelas mesmas bibliotecas da MaxMind **(verificar)**
  **MaxMind GeoLite2** (base local)  Gratuita, licença própria (**não** é open source) Exige cadastro, aceitar a licença e atualizar a base periodicamente **(verificar)**
  **IP2Location LITE** (base local)  Gratuita, licença própria            Formato e biblioteca próprios **(verificar)**
  **Não usar localização por IP**    Sem custo                             Válida: a usuária escolhe cidade/UF numa lista. É a mais simples e a mais privada

O IP também **não** deve ser enviado a APIs de terceiros (ipinfo,
ip-api etc.), mesmo as que têm plano gratuito: além dos limites, o IP da
usuária sairia do servidor. Com base local, **nenhum dado vai para
terceiros**. A leitura do `.mmdb` é feita por bibliotecas open source,
como o pacote `maxmind` para Node **(verificar licença)**.

### 5.3 Limitações da precisão

-   Resolve para o **provedor de internet**, não para a casa. Em rede
    móvel (CGNAT), o ponto pode estar a dezenas de quilômetros.
-   VPN, proxy e navegação "privada" por serviços intermediários falseiam
    o resultado.
-   Bases como a GeoLite2 trazem `accuracy_radius`; valores grandes
    indicam resultado pouco útil.
-   Deve ser tratado como **dica, não como fato**.

### 5.4 Obter o IP real atrás de proxy

O `req.ip` só reflete o IP real se o framework **confiar** no proxy
reverso (Nginx, load balancer, Cloudflare). Sem isso, o servidor vê o IP
do proxy; com configuração frouxa demais, um cliente pode forjar o
cabeçalho `X-Forwarded-For`.

``` ts
// Express
app.set('trust proxy', 1); // número de proxies confiáveis à frente da aplicação

// Nest com adaptador Express
const app = await NestFactory.create<NestExpressApplication>(AppModule);
app.set('trust proxy', 1);
```

O número correto depende da infraestrutura de implantação.

### 5.5 Exemplo com base local (`.mmdb`: DB-IP Lite ou GeoLite2)

``` ts
import maxmind, { CityResponse, Reader } from 'maxmind';

let leitor: Reader<CityResponse>;

export async function iniciarGeoIp() {
  leitor = await maxmind.open<CityResponse>('./data/GeoLite2-City.mmdb');
}

export function localizarPorIp(ip: string) {
  const r = leitor.get(ip);
  if (!r?.location) return null;
  return {
    cidade: r.city?.names?.['pt-BR'] ?? r.city?.names?.en ?? null,
    uf: r.subdivisions?.[0]?.iso_code ?? null,
    raioIncertezaKm: r.location.accuracy_radius ?? null,
    origem: 'ip' as const,
  };
}
```

A assinatura exata de `maxmind.open` varia entre versões do pacote
**(verificar)**. Retornar apenas cidade/UF, e **não** as coordenadas
aproximadas, reduz o risco de a informação ser tratada como precisa.

**Importante:** o IP é dado pessoal. Não gravá-lo em log nem no banco
(ver seção 10).

------------------------------------------------------------------------

## 6. Localização informada manualmente

É a alternativa indispensável quando a usuária nega a permissão, está em
desktop impreciso ou **prefere não compartilhar a posição exata**. Muitas
mulheres em situação de violência têm motivo para não querer ativar o
GPS.

### 6.1 CEP

``` text
Usuária digita CEP → front/back consulta base de CEP → obtém endereço
(e, se disponível, coordenadas) → busca serviços
```

-   Opções gratuitas: **BrasilAPI** (projeto de código aberto) e
    **ViaCEP** (API pública gratuita). A BrasilAPI pode devolver
    coordenadas, mas **nem sempre** há cobertura **(verificar)**.
-   Consultar a API pelo **back-end** evita expor o IP da usuária ao
    serviço externo e permite cache, mas faz o CEP passar pelo servidor.
-   Alternativa mais privada: manter localmente uma **tabela
    CEP → município/bairro** (ou apenas prefixo de CEP → município) e
    nunca chamar serviço externo.
-   Um CEP tem granularidade de rua ou até de endereço em alguns casos:
    é **mais identificador que uma coordenada arredondada**. Se possível,
    usar só os 5 primeiros dígitos (região).

### 6.2 Cidade/UF ou bairro

-   Mais simples e mais privado: lista de **municípios (IBGE)** com
    campo de busca/autocompletar, carregada do próprio projeto.
-   Para a primeira versão, **município + UF** costuma ser suficiente
    para exibir os serviços daquela cidade.

### 6.3 Geocodificação e geocodificação reversa

Converter endereço ↔ coordenadas exige um serviço de geocodificação.

  Opção                        Observações
  ---------------------------- ---------------------------------------------------------------
  **Base local do IBGE**       Malhas municipais + *point-in-polygon* (ex.: Turf.js) para descobrir o município a partir de coordenadas, sem chamar ninguém. Só resolve município, não endereço
  **Nominatim próprio**        Software livre sobre dados do OpenStreetMap, em servidor próprio. Resolve endereço, mas exige infraestrutura (disco e memória consideráveis para importar o Brasil) **(verificar)**
  **Photon** ou **Pelias**     Software livre de geocodificação sobre dados OSM; também exigem hospedagem própria
  Nominatim público (OSM)      Gratuito, mas com política de uso restritiva (limite de requisições, identificação obrigatória, sem uso intenso) **(verificar)**. Serve para protótipo; envia a consulta a terceiro

Para descobrir **em que município a usuária está** a partir de
coordenadas, o *point-in-polygon* com as malhas do IBGE resolve sem
terceiros. A geocodificação de endereço completo só seria necessária se o
projeto precisasse de rota ou de busca por rua, o que **não é o caso**.

------------------------------------------------------------------------

## 7. Arquitetura proposta

``` text
                      ┌───────────────────────────┐
                      │  React (navegador)        │
                      │                           │
  Usuária ─ clique ─► │  1. Geolocation API       │
  "perto de mim"      │     ou CEP / cidade       │
                      │  2. Arredonda coordenadas │
                      └─────────────┬─────────────┘
                                    │
              ┌─────────────────────┴─────────────────────┐
              │                                           │
              ▼ OPÇÃO A (mais privada)                    ▼ OPÇÃO B
   GET /servicos?uf=RS  (lista estática,            POST /servicos/proximos
   sem posição)                                     { lat, lng } arredondados
              │                                           │
              ▼                                           ▼
   Distância calculada no navegador              Back-end (Nest/Express)
   (Haversine)                                    valida → consulta → responde
                                                  sem registrar a posição
              │                                           │
              └─────────────────────┬─────────────────────┘
                                    ▼
                  Lista dos serviços mais próximos
                  (nome, endereço, telefone, distância)
```

### 7.1 Opção A: calcular no navegador

-   O back-end expõe a lista de serviços de uma UF/município (conteúdo
    estático, cacheável, **sem dados da usuária**).
-   O navegador pega a posição, calcula a distância (Haversine) e
    ordena.
-   **A posição nunca sai do dispositivo.** Não há o que vazar, logar ou
    intimar no servidor.
-   Viável enquanto a lista for pequena (centenas a poucos milhares de
    registros por UF).

### 7.2 Opção B: calcular no servidor

-   Necessária se a base for grande, se for preciso filtrar por critérios
    complexos ou se o projeto quiser medir uso.
-   Coordenadas **arredondadas** (2 casas decimais ≈ 1,1 km de latitude),
    enviadas por **POST**, nunca na URL.
-   Duas formas, ambas gratuitas e open source: **PostgreSQL + PostGIS**
    (`ST_DWithin`) ou, no protótipo, **Haversine em memória** sobre um
    JSON carregado na inicialização.

### 7.3 Recomendação

Começar pela **Opção A**. Migrar para B só se houver necessidade
concreta, e manter o mesmo contrato visual para a usuária.

------------------------------------------------------------------------

## 8. Implementação no front-end (React + TypeScript)

### 8.1 Hook de localização

``` tsx
import { useCallback, useState } from 'react';

export type EstadoLocalizacao =
  | { status: 'ocioso' }
  | { status: 'solicitando' }
  | { status: 'ok'; lat: number; lng: number; precisaoM: number }
  | { status: 'negado' }
  | { status: 'indisponivel' }
  | { status: 'tempo_esgotado' }
  | { status: 'nao_suportado' };

export function useLocalizacao() {
  const [estado, setEstado] = useState<EstadoLocalizacao>({ status: 'ocioso' });

  const solicitar = useCallback(() => {
    if (!('geolocation' in navigator)) {
      setEstado({ status: 'nao_suportado' });
      return;
    }
    setEstado({ status: 'solicitando' });

    navigator.geolocation.getCurrentPosition(
      (pos) =>
        setEstado({
          status: 'ok',
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          precisaoM: pos.coords.accuracy,
        }),
      (err) => {
        if (err.code === err.PERMISSION_DENIED) setEstado({ status: 'negado' });
        else if (err.code === err.TIMEOUT) setEstado({ status: 'tempo_esgotado' });
        else setEstado({ status: 'indisponivel' });
      },
      { enableHighAccuracy: false, timeout: 10_000, maximumAge: 5 * 60_000 },
    );
  }, []);

  return { estado, solicitar };
}
```

### 8.2 Uso na interface

``` tsx
function BuscarServicos() {
  const { estado, solicitar } = useLocalizacao();

  return (
    <section>
      <p>
        Posso mostrar serviços de apoio perto de você. Sua localização
        {' '}<strong>não será guardada</strong>.
      </p>

      <button onClick={solicitar} disabled={estado.status === 'solicitando'}>
        Usar minha localização
      </button>
      <button onClick={abrirFormularioManual}>Informar cidade ou CEP</button>

      {estado.status === 'negado' && (
        <p>
          Tudo bem, você não precisa compartilhar. Informe sua cidade ou CEP
          para continuar.
        </p>
      )}
      {/* demais estados tratados com a mesma lógica: sempre oferecer a alternativa manual */}
    </section>
  );
}
```

Diretrizes de interface:

-   **Pedir por clique**, com texto que explique *por que* e *o que
    acontece com o dado*, antes do prompt do navegador.
-   O botão manual (cidade/CEP) tem o **mesmo destaque** do botão de
    localização.
-   Nunca bloquear o resto da conversa por falta de localização.
-   Mensagens de erro sem culpa nem pressão.
-   Manter visível o botão de saída rápida e o banner 180/190/192.

### 8.3 Arredondamento e distância no cliente

``` ts
// 2 casas decimais ≈ 1,1 km em latitude (varia em longitude)
export const arredondar = (v: number, casas = 2) => Number(v.toFixed(casas));

export function haversineKm(
  a: { lat: number; lng: number },
  b: { lat: number; lng: number },
): number {
  const R = 6371;
  const rad = (g: number) => (g * Math.PI) / 180;
  const dLat = rad(b.lat - a.lat);
  const dLng = rad(b.lng - a.lng);
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}
```

Opção A completa:

``` ts
const servicos: Servico[] = await (await fetch('/api/servicos?uf=RS')).json();
const maisProximos = servicos
  .map((s) => ({ ...s, km: haversineKm(posicao, { lat: s.lat, lng: s.lng }) }))
  .sort((x, y) => x.km - y.km)
  .slice(0, 5);
```

------------------------------------------------------------------------

## 9. Implementação no back-end

Nest roda por padrão sobre o Express, então a lógica é a mesma. A
diferença é de organização.

### 9.1 NestJS

**DTO com validação** (`class-validator` / `class-transformer`):

``` ts
import { Type } from 'class-transformer';
import { IsInt, IsLatitude, IsLongitude, IsOptional, Max, Min } from 'class-validator';

export class BuscarServicosDto {
  @Type(() => Number) @IsLatitude()  lat: number;
  @Type(() => Number) @IsLongitude() lng: number;

  @IsOptional() @Type(() => Number) @IsInt() @Min(1) @Max(100)
  raioKm: number = 20;
}
```

**Controller** (POST, para as coordenadas não irem para a URL):

``` ts
@Controller('servicos')
export class ServicosController {
  constructor(private readonly servicos: ServicosService) {}

  @Post('proximos')
  @HttpCode(200)
  proximos(@Body() dto: BuscarServicosDto) {
    return this.servicos.buscarProximos(dto);
  }
}
```

**Habilitar a validação globalmente** em `main.ts`:

``` ts
app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));
```

**Service com PostGIS** (exemplo com `pg`/TypeORM `query`):

``` ts
async buscarProximos({ lat, lng, raioKm }: BuscarServicosDto) {
  return this.db.query(
    `SELECT id, nome, tipo, endereco, telefone,
            ST_Distance(geo, ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography) AS distancia_m
       FROM servicos
      WHERE ST_DWithin(geo, ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography, $3)
      ORDER BY distancia_m
      LIMIT 5`,
    [lng, lat, raioKm * 1000], // atenção: PostGIS usa (longitude, latitude)
  );
}
```

### 9.2 Express

``` ts
import express from 'express';
import { z } from 'zod';

const app = express();
app.set('trust proxy', 1);
app.use(express.json({ limit: '1kb' })); // payload minúsculo

const corpo = z.object({
  lat: z.number().min(-90).max(90),
  lng: z.number().min(-180).max(180),
  raioKm: z.number().int().min(1).max(100).default(20),
});

app.post('/servicos/proximos', async (req, res) => {
  const r = corpo.safeParse(req.body);
  if (!r.success) return res.status(400).json({ erro: 'parametros_invalidos' });

  const servicos = await buscarProximos(r.data);
  res.json(servicos);
});
```

### 9.3 Nest ou Express?

  Critério               Nest                                  Express
  ---------------------- ------------------------------------- -----------------------------
  Estrutura              Módulos, DI, validação integrada      Livre; você monta
  Curva de aprendizado   Maior                                 Menor
  Para este recurso      Mais código de base                   Poucas linhas bastam
  Escala do projeto      Melhor se o back-end crescer          Suficiente para um protótipo

Para este recurso não há diferença técnica relevante. A escolha deve
seguir o restante do back-end. Se o back-end for só um *gateway* para o
serviço Python dos modelos (FastAPI), **Express** tende a ser suficiente;
se houver vários módulos (sessões, conversas, serviços, auditoria),
**Nest** organiza melhor.

### 9.4 Base de serviços

-   Tabela `servicos` com: `id`, `nome`, `tipo`, `endereco`, `municipio`,
    `uf`, `telefone`, `horario`, `lat`, `lng`, `fonte`,
    `verificado_em`.
-   Dados **curados e versionados**, com fonte oficial e data de
    verificação, seguindo o mesmo princípio da base do RAG: **endereço e
    telefone nunca vêm da memória do LLM**.
-   Telefone e endereço errados são um risco real de segurança; a base
    precisa de revisão periódica.

------------------------------------------------------------------------

## 10. Privacidade, LGPD e segurança da usuária

Neste produto, **a localização é um dado de alto risco**: se o agressor
tem acesso ao dispositivo ou ao servidor, a localização pode revelar onde
a usuária está, ou onde pediu ajuda.

### 10.1 Princípios

1.  **Minimização:** coletar só se for necessário, no menor nível de
    detalhe útil (cidade/bairro, não endereço).
2.  **Finalidade única:** usar somente para listar serviços próximos.
    Nunca para análise, perfilamento ou pesquisa sem consentimento
    específico.
3.  **Consentimento específico e destacado**, em linguagem simples, no
    momento do pedido (e não escondido nos termos de uso).
4.  **Não armazenar** por padrão. Se o projeto precisar guardar (por
    exemplo, estatística), guardar apenas **município/UF**.
5.  **Alternativa sempre disponível** e sem penalização.

A LGPD não classifica localização como "dado sensível" no art. 5º, II,
mas dados sobre violência sofrida e saúde podem se enquadrar, e a
combinação com a localização aumenta o risco. Convém tratar a localização
com o mesmo rigor, e **validar o enquadramento jurídico** com quem
entende do assunto **(verificar)**.

### 10.2 Medidas técnicas

  Risco                                            Medida
  ------------------------------------------------ ---------------------------------------------------
  Coordenadas em log de acesso (nginx, proxy, APM) **POST com corpo**, nunca query string; não logar corpo; configurar *scrubbing* em ferramentas de erro/APM
  IP gravado em log                                Mascarar ou truncar IP nos logs (ex.: zerar o último octeto); retenção curta
  Servidor ou banco comprometido                   Não guardar a posição; se guardar, só município/UF
  Precisão excessiva                               Arredondar no cliente antes de enviar (≈ 1 km)
  Envio a terceiros                                Evitar APIs externas de IP, geocodificação e mapas; preferir bases locais
  Mapas/tiles de terceiros                         Carregar *tiles* (inclusive os do OSM) expõe o IP e a região visualizada; para a primeira versão, **mostrar lista, sem mapa**. Se houver mapa: Leaflet ou MapLibre com tiles próprios
  Scripts de terceiros na página                   `Permissions-Policy: geolocation=(self)` e CSP restritiva
  Cache do navegador/histórico                     Resposta com `Cache-Control: no-store` no endpoint de posição
  Descoberta do uso no dispositivo                 Aviso para usar modo anônimo; botão de saída rápida; sem notificações com conteúdo
  Rastreamento                                     Usar `getCurrentPosition`, nunca `watchPosition`

### 10.3 O pedido de permissão em si

-   A permissão fica **registrada no navegador** (por site). Quem tiver
    acesso ao aparelho pode ver nas configurações que o site tem
    permissão de localização. Isso pode ser um sinal para o agressor.
-   Se possível, **não manter a permissão salva** (alguns navegadores
    permitem "apenas desta vez"), e orientar a usuária a revogá-la.
-   Ou seja: a Opção A (cálculo no navegador) **não elimina** esse
    rastro no dispositivo; só elimina o rastro no servidor.

### 10.4 Rota de emergência e localização

-   Em emergência, **não solicitar localização antes de mostrar
    190/180/192**. O prompt do navegador, a espera e uma eventual
    negação **atrasam** a informação mais importante.
-   O sistema **não aciona a polícia** com base na localização, e a
    interface **não deve sugerir** que "ajuda foi enviada".
-   Depois dos canais de emergência, a busca de serviços próximos pode
    ser **oferecida** como próximo passo, nunca imposta.

------------------------------------------------------------------------

## 11. Integração com o chatbot

-   O motor de política (seção 3.6 da arquitetura) pode incluir uma ação
    **"oferecer serviços próximos"**, disparada quando a conversa indicar
    interesse em procurar ajuda presencial ou quando o risco for ≥ 3.
-   A **resposta com os serviços é montada por template** a partir da
    base curada, e não escrita pelo LLM, mantendo a garantia contra
    alucinação de endereços e telefones.
-   O validador de saída deve checar que todo endereço/telefone da
    resposta existe na tabela `servicos`.
-   A localização **não entra** nos classificadores nem no resumo da
    conversa (seção 14 da arquitetura). Se for preciso registrar algo,
    apenas `localizacao_oferecida: true/false` e o `uf`.
-   Se a usuária **escrever** onde mora ("moro em Canoas"), um extrator
    de entidades pode sugerir o município, que deve ser **confirmado**
    antes de ser usado.

------------------------------------------------------------------------

## 12. Casos de borda e testes

### 12.1 Casos de borda

  Caso                                          Comportamento esperado
  --------------------------------------------- ------------------------------------------------
  Permissão negada                              Fluxo manual, sem insistência
  Permissão já bloqueada no navegador           Explicar como alterar, ou usar cidade/CEP
  Timeout                                       Botão "tentar de novo" + alternativa manual
  Desktop com `accuracy` muito alta (km)        Avisar que a posição é aproximada; confirmar cidade
  Sem serviços no raio                          Ampliar o raio, mostrar o mais próximo e **sempre** o 180
  Coordenadas fora do Brasil                    Mensagem clara; manter 180 como referência nacional
  VPN ou IP incoerente                          Não usar IP como dado definitivo; pedir confirmação
  Resposta lenta/offline                        Mostrar o 180/190 e a opção manual
  Sem JavaScript / navegador antigo             Formulário manual funcional
  Coordenadas inválidas (`lat = 999`)           400 na validação, sem detalhes internos

### 12.2 Testes automatizados

-   **Front:** simular a Geolocation API (mock de `navigator.geolocation`
    nos testes unitários); no Playwright, `context.grantPermissions(['geolocation'])`
    e `context.setGeolocation({ latitude, longitude })`. Testar também o
    caso sem permissão.
-   **Back:** testes de validação do DTO/zod, consulta com banco de
    teste (PostGIS) e limites (raio mínimo/máximo, coordenadas nos polos
    e na linha de data).
-   **Privacidade:** teste que **falha** se coordenadas aparecerem em
    logs (capturar a saída de log durante os testes e procurar o valor
    enviado).
-   **Manual:** DevTools → Sensors, para emular posições e erros.
-   **Dispositivos reais:** Android/Chrome, iOS/Safari e um webview de
    app de mensagens.

------------------------------------------------------------------------

## 13. Comparação das abordagens

  Abordagem                                  Precisão   Privacidade   Esforço   Recomendação
  ------------------------------------------ ---------- ------------- --------- ---------------------------
  Geolocation API + cálculo no navegador     Alta       **Muito alta** Baixo    **Principal**
  Geolocation API + cálculo no servidor      Alta       Média         Médio     Se a base crescer
  CEP / cidade manual                        Média      Alta          Baixo     **Alternativa obrigatória**
  IP com base local (DB-IP Lite / GeoLite2)  Baixa      Média         Médio     Só como sugestão
  Município por malhas do IBGE (local)       Município  Alta          Médio     Alternativa à geocodificação
  Nominatim/Photon próprio                   Endereço   Alta          Alto      Só se precisar de endereço
  Nominatim público                          Endereço   Baixa         Baixo     Apenas protótipo

------------------------------------------------------------------------

## 14. Limitações e riscos

-   **A localização pode não estar disponível**, e o produto precisa
    funcionar plenamente sem ela.
-   **A precisão varia muito** (GPS no celular vs. Wi-Fi/IP no desktop).
    Mostrar a distância como aproximada.
-   **Rastro no dispositivo:** a permissão salva no navegador e o histórico
    podem denunciar o uso.
-   **Qualidade da base de serviços:** o valor da funcionalidade depende
    de endereços e telefones corretos e atualizados; um dado desatualizado
    pode levar a usuária a um lugar fechado ou inexistente.
-   **Dependência de licenças e termos de terceiros** (bases de IP,
    CEP, geocodificação), que devem ser verificados.
-   **Risco jurídico:** o tratamento de dados de localização de vítimas
    exige base legal clara e, em uso real, respaldo institucional.
-   O protótipo acadêmico **não deve ser divulgado como serviço de
    atendimento** sem esse respaldo (ver seção 11 da arquitetura).

------------------------------------------------------------------------

## 15. Próximos passos sugeridos

1.  Definir **escopo geográfico** inicial (ex.: RS ou um conjunto de
    municípios) para viabilizar a base de serviços.
2.  Montar a **base curada de serviços**, com fonte e data de verificação.
3.  Implementar o **protótipo da Opção A** (hook + lista estática +
    Haversine), com fluxo manual por município.
4.  Adicionar a **busca por CEP/cidade** com base local.
5.  Executar a **checklist de privacidade** (seção 10.2) e o teste de
    logs.
6.  Testar em **dispositivos reais**, incluindo webviews.
7.  Só então avaliar se a **Opção B (servidor)** ou a geolocalização por
    IP agregam valor suficiente para justificar o risco.

### Possível pergunta de pesquisa

> **"Em que medida o cálculo de proximidade no dispositivo, sem envio da
> posição ao servidor, preserva a utilidade da indicação de serviços de
> atendimento a mulheres em situação de violência, em comparação com o
> cálculo no servidor?"**

------------------------------------------------------------------------

## 16. Conclusão

Obter a localização em uma aplicação React com back-end Nest ou Express é
tecnicamente simples: a **Geolocation API** resolve a maior parte dos
casos em poucas linhas, e o back-end só precisa validar a entrada e,
opcionalmente, consultar uma base geográfica. A diferença entre Nest e
Express é de organização, não de capacidade.

A parte difícil não é técnica. Em um produto voltado a mulheres em
situação de violência, a decisão central é **quanta localização o sistema
precisa receber e guardar**. A recomendação é:

1.  **Pedir só por ação explícita**, explicando o motivo.
2.  **Oferecer sempre a alternativa manual** (cidade/CEP).
3.  **Calcular a proximidade no navegador**, de modo que a posição não
    chegue ao servidor.
4.  **Se chegar ao servidor:** coordenadas arredondadas, por POST, sem log
    e sem persistência.
5.  **Usar IP apenas como pista grosseira**, com base local.
6.  **Servir endereços e telefones de base curada**, nunca do LLM.
7.  **Não condicionar a rota de emergência à localização.**

Com isso, a funcionalidade entrega o benefício (levar a usuária a um
serviço real e próximo) com o menor risco possível para a sua segurança.
