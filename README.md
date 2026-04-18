# driftwatch

> CLI tool to detect and report configuration drift across cloud environments

---

## Installation

```bash
pip install driftwatch
```

Or install from source:

```bash
git clone https://github.com/yourorg/driftwatch.git && cd driftwatch && pip install .
```

---

## Usage

```bash
# Scan your cloud environment for configuration drift
driftwatch scan --provider aws --region us-east-1

# Compare current state against a saved baseline
driftwatch compare --baseline ./baseline.json --output report.html

# Watch for drift continuously and alert on changes
driftwatch watch --interval 300 --notify slack
```

**Example output:**

```
[✓] Scanning AWS us-east-1...
[!] Drift detected in 3 resources:
    - ec2/i-0abc123: security group modified
    - s3/my-bucket: public access policy changed
    - iam/role-prod: inline policy added

Report saved to: drift-report-2024-01-15.html
```

---

## Configuration

Create a `driftwatch.yml` in your project root to define environments, providers, and alerting rules. See [docs/configuration.md](docs/configuration.md) for full reference.

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any major changes.

---

## License

[MIT](LICENSE)