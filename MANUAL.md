
# Phashcat — Monoid-style Hashcat Builder

A tiny, immutable, fluent wrapper around the `hashcat` CLI.

- **Install**: `pip install "https://github.com/avitwil/Phashcat/releases/download/v0.1.1/phashcat-0.1.1-py3-none-any.whl"`
- **Repo**: https://github.com/avitwil/Phashcat
- **Author**: Avi Twil

> **Import once, from one place**
>
> ```python
> from Phashcat import hashcat, flags
> ```
>
> - `hashcat(...)` → factory that returns a `HashcatBuilder`
> - `flags` → constants/tables (e.g., `flags.ATTACK_MODES`, `flags.VALUE_KIND`)

> **Note on binaries**  
> Phashcat calls your system’s Hashcat binary.  
> If auto-detection fails, either:
> - pass `binary="path/to/hashcat"` to `hashcat(...)`, or
> - set `HASHCAT_BINARY=/path/to/hashcat` in your environment.

---

## Installation
> ```cli
> pip install "https://github.com/avitwil/Phashcat/releases/download/v0.1.1/phashcat-0.1.1-py3-none-any.whl"
> --or--
> pip install Phashcat
> ```
## Core Concepts

---

### Monoid Design
- **Identity**: `HashcatBuilder.empty()` is the neutral element.
- **Append**: `.mappend(other)` combines two builders (right-biased override).
- **Associativity**: `(a⊕b)⊕c == a⊕(b⊕c)`.

### Immutability
Every method returns a **new** builder. Your previous builder remains unchanged.

```python
from Phashcat import hashcat

base = hashcat("hashes.txt")
b1 = base.hash_type(0)
b2 = base.hash_type(1000)
# base is unchanged; b1 and b2 are different immutable variants
````

---

## Quick Start

```python
from Phashcat import hashcat

cmd = (
    hashcat("example0.hash", "?d?d?d?d?d?d")
    .hash_type(0)      # -m 0 (MD5)
    .attack_mode(3)    # -a 3 (Brute-force / mask)
    .outfile("cracked.txt")
    .status(True).status_timer(2)
    .workload_profile(3)   # High
    .value()
)

# import subprocess; subprocess.run(cmd, check=True)
```

---

## API Surface (Fluent Methods)

Each call returns a **new** `HashcatBuilder`:

* **Modes & basics**
  `.hash_type(num)`, `.attack_mode(num)`, `.outfile(path)`, `.status(on=True)`, `.status_timer(seconds)`
* **Workload & Markov**
  `.workload_profile(w)`, `.markov_threshold(x)`, `.session(name)`, `.runtime(seconds)`
* **Candidate window**
  `.skip(n)`, `.limit(n)`
* **Rules**
  `.rules_file(path)`, `.rule_left(rule)`, `.rule_right(rule)`, `.generate_rules(n)`
* **Mask / increment**
  `.increment(on=True)`, `.increment_min(n)`, `.increment_max(n)`
* **Charsets**
  `.cs1(cs)` … `.cs8(cs)`  → define `?1.. ?8`
* **Encoding & Potfile**
  `.encoding_from(code)`, `.encoding_to(code)`, `.potfile_path(path)`, `.potfile_disable(on=True)`
* **Backend & perf**
  `.backend_devices(csv)`, `.opencl_device_types(csv)`, `.backend_info(on=True)`,
  `.kernel_accel(n)`, `.kernel_loops(n)`, `.kernel_threads(n)`, `.vector_width(n)`,
  `.optimized_kernel(on=True)`, `.multiply_accel_disable(on=True)`, `.cpu_affinity(csv)`, `.hook_threads(n)`
* **Brain & QoL**
  `.brain_client(on=True)`, `.brain_server(on=True)`, `.brain_host(host)`, `.brain_port(port)`, `.brain_password(pwd)`,
  `.color_cracked(on=True)`, `.quiet(on=True)`, `.force(on=True)`, `.show(on=True)`, `.left(on=True)`, `.stdout(on=True)`
* **Generic controls**
  `.set(flag, value=True)`, `.unset(flag)`, `.arg(*args)`  (positional operands)
* **Monoid & execution**
  `.mappend(other)`, `.value()`, `.cmdline()`, `.run(check=True, capture_output=False, text=True)`

> Advanced flags which do not have a dedicated method can always be set via
> `builder.set(flags.SOME_FLAG, value_or_bool)`.

Tables (read-only):
`flags.ATTACK_MODES`, `flags.OUTFILE_FORMATS`, `flags.RULE_DEBUG_MODES`,
`flags.BRAIN_CLIENT_FEATURES`, `flags.BUILTIN_CHARSETS`,
`flags.OPENCL_DEVICE_TYPES`, `flags.WORKLOAD_PROFILES`, `flags.VALUE_KIND`.

---

## Full Examples

> In all examples:
>
> ```python
> from Phashcat import hashcat, flags
> ```
>
> Replace sample files (`example0.hash`, `example.dict`, etc.) with your own.

### 1) Straight Wordlist (Attack `-a 0`)

MD5 hashes from `example0.hash`, using `example.dict`, write results to `out.txt`.

```python
cmd = (
    hashcat("example0.hash", "example.dict")
    .hash_type(0)            # MD5
    .attack_mode(0)          # straight wordlist
    .outfile("out.txt")
    .status(True).status_timer(2)
    .workload_profile(2)     # Default
    .value()
)
```

### 2) Wordlist + Rules

Apply the popular `best64.rule`.

```python
cmd = (
    hashcat("example0.hash", "example.dict")
    .hash_type(0)
    .attack_mode(0)
    .rules_file("rules/best64.rule")
    .outfile("out_rules.txt")
    .status(True)
    .value()
)
```

### 3) Brute-force Mask (Attack `-a 3`)

Six printable ASCII characters (mask `?a?a?a?a?a?a`).

```python
cmd = (
    hashcat("example0.hash", "?a?a?a?a?a?a")
    .hash_type(0)
    .attack_mode(3)
    .outfile("out_bruteforce.txt")
    .status(True)
    .workload_profile(3)     # High
    .value()
)
```

#### 3.1) Incremental Mask

Start at length 4, stop at 6.

```python
cmd = (
    hashcat("example0.hash", "?1?1?1?1?1?1")
    .hash_type(0).attack_mode(3)
    .cs1("?l?d")             # define ?1 = lower+digit
    .increment(True).increment_min(4).increment_max(6)
    .outfile("out_inc.txt")
    .value()
)
```

### 4) Hybrid Wordlist + Mask (Attack `-a 6`)

Append a 2-digit number to each word (e.g., `password12`).

```python
cmd = (
    hashcat("example0.hash", "example.dict", "?d?d")
    .hash_type(0)
    .attack_mode(6)
    .outfile("out_hybrid6.txt")
    .status(True)
    .value()
)
```

### 5) Hybrid Mask + Wordlist (Attack `-a 7`)

Prepend a 2-digit number to each word (e.g., `12password`).

```python
cmd = (
    hashcat("example0.hash", "?d?d", "example.dict")
    .hash_type(0)
    .attack_mode(7)
    .outfile("out_hybrid7.txt")
    .value()
)
```

### 6) Combination (Attack `-a 1`)

Combine words from two dictionaries (concatenation).

```python
cmd = (
    hashcat("example0.hash", "left.dict", "right.dict")
    .hash_type(0)
    .attack_mode(1)
    .outfile("out_combo.txt")
    .value()
)
```

### 7) Association (Attack `-a 9`)

Requires a rule to associate (see hashcat docs). Example skeleton:

```python
cmd = (
    hashcat("example500.hash", "1word.dict")
    .hash_type(500)          # $1$ example
    .attack_mode(9)
    .rules_file("rules/best64.rule")
    .outfile("out_assoc.txt")
    .value()
)
```

### 8) Show / Left (Potfile reconciliation)

* `--show`: show cracked hashes using potfile
* `--left`: show uncracked hashes using potfile

```python
show_cmd = (
    hashcat("hashes.txt")
    .show(True)
    .potfile_path("my.pot")   # optional; default potfile otherwise
    .value()
)

left_cmd = (
    hashcat("hashes.txt")
    .left(True)
    .value()
)
```

### 9) Identify Supported Algorithms for Input Hashes

`--identify` is a switch that expects the hash file as a positional after it.

```python
cmd = (
    hashcat()
    .set(flags.IDENTIFY, True)   # emits: --identify
    .arg("my.hash")              # positional file to analyze
    .value()
)
```

### 10) Sessions & Restore

Start a named session:

```python
session_cmd = (
    hashcat("example0.hash", "example.dict")
    .hash_type(0).attack_mode(0)
    .session("mysession")
    .outfile("out.txt")
    .value()
)
```

Resume from a session:

```python
restore_cmd = (
    hashcat()
    .session("mysession")
    .set(flags.RESTORE, True)    # --restore
    .value()
)
```

### 11) Benchmark & Backend Info

```python
benchmark = hashcat().set(flags.BENCHMARK, True).value()          # -b
backend_info = hashcat().backend_info(True).value()               # -I
```

### 12) Brain Client/Server (Distributed Guessing)

*(Read hashcat docs for network & security caveats.)*

```python
server = (
    hashcat()
    .brain_server(True)
    .brain_server_timer(300)     # .set(flags.BRAIN_SERVER_TIMER, 300) if needed
    .value()
)

client = (
    hashcat("example0.hash", "example.dict")
    .hash_type(0).attack_mode(0)
    .brain_client(True)
    .brain_host("127.0.0.1").brain_port(13743).brain_password("secret")
    .outfile("out_brain.txt")
    .value()
)
```

### 13) Potfile / Encoding Tweaks

```python
cmd = (
    hashcat("example0.hash", "example.dict")
    .hash_type(0).attack_mode(0)
    .encoding_from("iso-8859-15").encoding_to("utf-32le")
    .potfile_path("custom.pot")
    .value()
)
```

### 14) Backend Tuning

```python
cmd = (
    hashcat("example0.hash", "?a?a?a?a")
    .hash_type(0).attack_mode(3)
    .optimized_kernel(True)
    .kernel_accel(64).kernel_loops(256).kernel_threads(64)
    .opencl_device_types("2")        # GPU
    .backend_devices("1,2")          # select specific devices
    .value()
)
```

### 15) Compose with Monoid (`.mappend`)

Build reusable presets and combine them.

```python
preset_md5  = hashcat().hash_type(0)
preset_mask = hashcat().attack_mode(3).workload_profile(3)

cmd = (
    preset_md5
    .mappend(preset_mask)
    .outfile("out.txt")
    .arg("example0.hash", "?a?a?a?a?a?a")
    .status(True)
    .value()
)
```

### 16) Execute Directly

All builders support `.run(...)`.

```python
result = (
    hashcat("example0.hash", "example.dict")
    .hash_type(0).attack_mode(0)
    .outfile("out.txt")
    .run(check=False, capture_output=True)
)

print(result.returncode)
print(result.stdout[:500])
print(result.stderr[:500])
```

---

## Tips & Notes

* Prefer `.value()` (argv list) with `subprocess.run` for safety.
* Use `.set(...)` for any advanced flag that doesn’t have a dedicated method.
* Keep legality and ethics in mind: use hashcat only on hashes you are permitted to test.

---

## Troubleshooting

* **Binary not found**: set `HASHCAT_BINARY` or pass `binary="..."` to `hashcat(...)`.
* **Non-zero exit**: use `.run(check=False, capture_output=True)` to inspect stderr.
* **Performance tuning**: see `flags.WORKLOAD_PROFILES` and the hashcat wiki for guidance.

