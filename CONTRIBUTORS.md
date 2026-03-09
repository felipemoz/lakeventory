# Contributors Guide

Este repositório segue um fluxo simples e objetivo para contribuições.

## Regra Padrão de Issue

Toda mudança deve começar por uma Issue.

### Estrutura mínima obrigatória da Issue

- **Título claro**: verbo no imperativo + objeto (ex.: "Adicionar validação de permissões na CLI").
- **Contexto**: qual problema real está sendo resolvido.
- **Objetivo**: resultado esperado da mudança.
- **Escopo**:
  - **Inclui**: o que será feito.
  - **Não inclui**: o que não será feito (evitar scope creep).
- **Critérios de aceite**: checklist verificável.
- **Riscos e impacto**: segurança, compatibilidade, performance.
- **Plano de validação**: como testar (comandos, cenários, dados).

### Regras

- 1 Issue = 1 problema/entrega principal.
- Sem Issue, sem PR.
- Toda PR deve referenciar uma Issue (`Closes #<id>` ou `Refs #<id>`).
- Mudanças grandes devem ser quebradas em Issues menores.

---

## Boas Práticas de Contribuição

### Código

- Faça mudanças pequenas e focadas.
- Corrija a causa raiz, não só o sintoma.
- Preserve estilo e padrões já existentes no projeto.
- Evite renomeações/refactors desnecessários fora do escopo.

### Testes

- Adicione ou atualize testes quando a mudança alterar comportamento.
- Rode testes relevantes antes de abrir PR.
- Não quebre testes existentes sem justificativa explícita.

### Segurança

- Nunca commitar segredos (`.env`, tokens, chaves).
- Não expor credenciais em logs, exemplos ou screenshots.
- Revisar entradas de usuário e tratamento de erro para evitar vazamento de dados.

### Documentação

- Atualize documentação quando alterar interface, flags ou fluxo de uso.
- Prefira instruções executáveis e exemplos reais.
- Mantenha README enxuto; detalhes ficam em `docs/`.

### Commits e PRs

- Commits com mensagem clara e objetiva.
- PR deve conter:
  - resumo da mudança,
  - motivação,
  - evidência de testes,
  - impactos e rollback (se aplicável).

---

## Checklist rápido antes do PR

- [ ] Issue criada e referenciada.
- [ ] Escopo validado (sem extras não planejados).
- [ ] Testes executados e passando.
- [ ] Sem segredos/versionamento indevido.
- [ ] Documentação atualizada.
- [ ] Mudança pronta para review.

---

## Como começar

1. Abra a Issue com o template acima.
2. Crie branch a partir da `main`.
3. Implemente em incrementos pequenos.
4. Rode testes e validações.
5. Abra PR referenciando a Issue.
