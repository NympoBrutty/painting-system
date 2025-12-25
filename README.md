# Stage A — Contract Canon

Stage A є **єдиним джерелом істини** для проекту «малювання».

Він визначає:
- Структуру модулів та їхні типи (PROCESS / RULESET / BRIDGE)
- Входи та виходи (io_contract)
- Параметри з одиницями вимірювання та діапазонами
- Обмеження (constraints) та правила валідації
- Алгоритм виконання з data flow
- Канон контрактів (незалежний від реалізацій)

Stage A **не містить реалізацій** і **не прив'язаний до конкретного рушія**  
(Python / AI / інше — це наступні стадії).

## Версія

- **Package Version:** 4.1.0
- **Schema Version:** 4.0.0
- **Catalog Version:** 4.0.0
- **Контракти:** 3 пілотних модулі

## Швидкий старт

### Одна кнопка (рекомендовано)

```bash
# Запустити всю валідацію локально
python run_stageA.py

# Швидка перевірка (без тестів)
python run_stageA.py --quick

# Детальний вивід
python run_stageA.py --verbose
```

### Окремі команди

```bash
# Валідація всіх контрактів
python stageA/tools/batch_validator.py stageA/contracts \
    --glossary stageA/glossary/glossary_v1.json \
    --schema stageA/schema/contract_schema_stageA_v4.json \
    --out stageA/_reports

# Запуск тестів
python -m unittest discover -s stageA/tests -p "test_*.py" -v
```

## Як додати новий контракт

### Крок 1: Згенеруй шаблон

```bash
python stageA/tools/generate_from_template.py \
    --module-id A-V-1 \
    --module-abbr TONE \
    --module-type PROCESS \
    --module-name-uk "ТОНАЛЬНА КАРТА" \
    --module-name-en "TONE MAP" \
    --out stageA/contracts/A-V-1_TONE_contract_stageA_FINAL.json
```

### Крок 2: Заповни контракт

Відкрий згенерований файл і заміни всі `TODO:` на реальні дані:
- `description` — детальний опис модуля
- `io_contract` — входи та виходи
- `parameters` — параметри з типами та діапазонами
- `constraints` — жорсткі обмеження
- `validation.rules` — м'які правила (warnings)
- `algorithm.steps` — кроки виконання
- `test_cases` — тестові сценарії

### Крок 3: Валідуй

```bash
python run_stageA.py
```

### Крок 4: Додай до каталогу

Відредагуй `stageA/katalog/katalog_4_0.json` — додай новий модуль до масиву `modules`.

### Крок 5: Оновлення глосарію (за потреби)

Якщо використовуєш нові терміни/абревіатури — додай їх до `stageA/glossary/glossary_v1.json`.

### Крок 6: Коміт

```bash
git add .
git commit -m "feat(stageA): add A-V-1 TONE contract"
git push
```

## Структура репозиторію

```
painting-system/
├── README.md
├── run_stageA.py          # ← Одна кнопка запуску
├── requirements.txt
├── .gitignore
├── .github/
│   └── workflows/
│       └── stageA-ci.yml
└── stageA/
    ├── __init__.py        # ← Python package
    ├── contracts/
    │   ├── A-I-3_SPS_contract_stageA_FINAL.json
    │   ├── A-III-2_NSS_contract_stageA_FINAL.json
    │   └── A-IV-2_LINE_contract_stageA_FINAL.json
    ├── schema/
    │   └── contract_schema_stageA_v4.json
    ├── katalog/
    │   └── katalog_4_0.json
    ├── glossary/
    │   └── glossary_v1.json
    ├── lint/
    │   ├── __init__.py
    │   ├── contract_lint_validator.py
    │   └── LINT_SPEC_STAGE_A.md
    ├── tools/
    │   ├── __init__.py
    │   ├── batch_validator.py
    │   └── generate_from_template.py
    └── tests/
        ├── __init__.py
        └── test_stageA_contracts.py
```

## Пілотні модулі

| ID | Abbr | Type | Назва | Опис |
|----|------|------|-------|------|
| A-I-3 | SPS | BRIDGE | Shot / Plan System | Канонічна система планів і кадрування |
| A-III-2 | NSS | RULESET | Negative Space System | Аналіз негативного простору |
| A-IV-2 | LINE | PROCESS | Line Engine | Нормалізація контурних ліній |

## Contract File Naming Convention

**Обов'язковий формат:**
```
A-<BLOCK>-<NUM>_<ABBR>_contract_stageA_FINAL.json
```

**Приклади:**
- `A-I-3_SPS_contract_stageA_FINAL.json` ✅
- `A-III-2_NSS_contract_stageA_FINAL.json` ✅
- `my_contract.json` ❌

**Що НЕ є контрактом (ігнорується валідатором):**
- `katalog_*.json`
- `glossary_*.json`
- `contract_schema_*.json`
- `*_report.json`
- `*_lint.json`
- `summary.json`

## Типи модулів

| Тип | Призначення |
|-----|-------------|
| **PROCESS** | Генеративні модулі — створюють нові артефакти |
| **RULESET** | Валідаційні модулі — перевіряють правила |
| **BRIDGE** | Mapping модулі — з'єднують різні системи |

## Constraints DSL

Формат виразів (syntax: `string_expr`):

```json
{
  "expr": "shot_type == 'ECU' => framing_tightness >= 0.85",
  "error_code": "E001"
}
```

Підтримувані оператори:
- Порівняння: `==`, `!=`, `>`, `>=`, `<`, `<=`
- Логічні: `&&`, `||`, `!`
- Імплікація: `=>`

## Версіонування

| Що | Формат | Приклад |
|----|--------|---------|
| Package version | SemVer | 4.1.0 |
| Schema version | SemVer | 4.0.0 |
| Contract version | SemVer | 1.1.0 |
| Maturity stage | enum | pilot → draft → stable |

## CI/CD

GitHub Actions автоматично:
1. ✅ Валідує всі контракти
2. ✅ Запускає unit тести
3. ✅ Зберігає звіти як artifacts

Звіти доступні у вкладці Actions → Artifacts.

---

**Stage A — це канон,  
Stage B+ — це реалізації.**

## Ліцензія

MIT License
