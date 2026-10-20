# Lab 03 - Task 2: Breaking the service

The requests below were run against the unmodified starter service on
`localhost:8018` on 2026-10-20. For each scenario, the service was restarted
when the task says to restart it.

## (a) Unknown student

Command:

```powershell
curl.exe -i http://localhost:8018/students/NOPE
```

Result: HTTP 200 with `{"error": "not found"}`. The server did not log an error.
The expected result is a not-found status, not 200.

## (b) JSON body is the number 5

Command:

```powershell
curl.exe -i -X POST http://localhost:8018/students -H "Content-Type: application/json" -d "5"
```

Result: `curl` reported `(52) Empty reply from server`. The server raised
`TypeError: argument of type 'int' is not iterable` while checking for the
`id` field in `do_POST`.

## (c) Non-numeric score

Commands:

```powershell
curl.exe -i -X POST http://localhost:8018/students -H "Content-Type: application/json" -d '{"id":"S1","name":"Ayesha"}'
curl.exe -i -X POST http://localhost:8018/assessments -H "Content-Type: application/json" -d '{"id":"A1","title":"Quiz 1","weight":"10","total":"20"}'
curl.exe -i -X POST http://localhost:8018/marks -H "Content-Type: application/json" -d '{"student":"S1","assessment":"A1","score":"abc"}'
curl.exe -i http://localhost:8018/students/S1
```

Results: the student, assessment, and mark requests each returned HTTP 200.
The mark was saved even though its score was `"abc"`. The student GET got no
reply (`curl` error 52); the server raised
`ValueError: could not convert string to float: 'abc'` while calculating the
percentage.

## (d) Zero assessment total

The service was stopped, `gradebook.json` was deleted, and the service was
restarted before these commands:

```powershell
curl.exe -i -X POST http://localhost:8018/students -H "Content-Type: application/json" -d '{"id":"S1","name":"Ayesha"}'
curl.exe -i -X POST http://localhost:8018/assessments -H "Content-Type: application/json" -d '{"id":"A0","title":"Zero","weight":"10","total":"0"}'
curl.exe -i -X POST http://localhost:8018/marks -H "Content-Type: application/json" -d '{"student":"S1","assessment":"A0","score":"0"}'
curl.exe -i http://localhost:8018/report
```

Results: all three POST requests returned HTTP 200 and the invalid assessment
and mark were saved. The report GET got no reply (`curl` error 52); the server
raised `ZeroDivisionError: float division by zero`.

## (e) Mark for an unknown assessment

The service was stopped, `gradebook.json` was deleted again, and the service
was restarted. A student was created because the starter checks that the
student exists before recording a mark.

Commands:

```powershell
curl.exe -i -X POST http://localhost:8018/students -H "Content-Type: application/json" -d '{"id":"S1","name":"Ayesha"}'
curl.exe -i -X POST http://localhost:8018/marks -H "Content-Type: application/json" -d '{"student":"S1","assessment":"NOPE","score":"1"}'
```

Results: both requests returned HTTP 200. The mark for the unknown assessment
was accepted and saved; the server logged `recorded mark for S1 score 1`.

`gradebook.json` stores state across restarts. Deleting it was necessary to
start each scenario with a clean gradebook, avoid conflicts with previously
created students and assessments, and reproduce the lab's first-run condition.

## Ruff and bare `except` findings

Command:

```powershell
ruff check .
```

Result: Ruff reported 8 errors (2 auto-fixable): unsorted imports, unused
`os`, non-context-managed file opens, three bare `except` clauses, and a
`try`/`except` that silently ignores errors.

Bare `except` line numbers in `gradebook.py`: **19, 28, and 84**.

## Task 8: Repeat of the failure requests after the fixes

These requests were repeated with the updated service on 2026-10-20. The
service used a temporary working directory so the checks did not change the
project's gradebook data.

| Case | Request | Result |
|---|---|---|
| (a) | `curl.exe -i http://localhost:<port>/students/NOPE` | HTTP 404, `{"error": "student not found"}` |
| (b) | `curl.exe -i -X POST http://localhost:<port>/students -H "Content-Type: application/json" -d "5"` | HTTP 400, `{"error": "request body must be a JSON object"}` |
| (c) | Create student S1 and assessment A1 using the README request bodies, then POST a mark with score `"abc"` | Student and assessment returned HTTP 200; invalid mark returned HTTP 400, `{"error": "score must be a finite number"}` |
| (c) | `curl.exe -i http://localhost:<port>/students/S1` | HTTP 200; percentage was `"0"`, confirming the rejected mark was not saved |
| (d) | After deleting the temporary `gradebook.json` and restarting, create S1, then create assessment A0 with total `"0"` | Student returned HTTP 200; invalid assessment returned HTTP 400, `{"error": "total must be above 0"}` |
| (d) | POST a mark for S1 and the rejected A0, then GET `/report` | Mark returned HTTP 404, `{"error": "assessment not found"}`; report returned HTTP 200 with S1 at `"0"` percent |
| (e) | After deleting the temporary `gradebook.json` and restarting, create S1, then POST a mark for assessment NOPE | Student returned HTTP 200; mark returned HTTP 404, `{"error": "assessment not found"}` |

No request crashed the server. These outcomes show that malformed values and
unknown resources are now rejected before they can corrupt stored gradebook
data.
