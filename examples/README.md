# Examples

The following are a some good samples to start taking screenshots of

- [Fetch frontpages of some newssites every hour](newssites.txt)

```bash
saas newssites.txt mount/ --ignore-found-urls --refresh-rate=hour
```

- [A little less image heavy sample](lightweight.txt)

```bash
saas lightweight.txt mount/ --stay-at-domain --refresh-rate=day
```

- [Link sharing sites that will quickly build a random sample](random.txt)

```bash
saas random.txt mount/ --refresh-rate=day
```
