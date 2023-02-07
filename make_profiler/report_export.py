from datetime import datetime
import json
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

status_list = {}
status = []


def export_report(performance, docs, targets):
    strOutputFile = 'report.json'
    fo = open(strOutputFile, 'w', encoding="utf-8")
    n_in_progress = 0
    n_failed = 0
    n_total = 0
    oldest_completed_target = ''

    not_started_targets = set(targets)

    for key in performance:
        not_started_targets.remove(key)

        rec = performance[key]
        n_total += 1
        if rec["failed"]:
            event_type = "failed"
            n_failed += 1
        elif rec["done"]:
            event_type = "completed"
        elif rec["running"]:
            event_type = "started"
            n_in_progress += 1
        else:
            # this usually occurs when target is completed, but corresponding file or folder is not found.
            event_type = "completed with no output"

        if 'start_current' in rec and rec["done"]:
            last_event_time = datetime.utcfromtimestamp(
                int(rec['finish_current'])).strftime(DATE_FORMAT)
        elif 'start_current' in rec and not rec["done"] and not rec["running"] and not rec["failed"]:
            # this is the case of undefined status, "completed with no output"
            last_event_time = datetime.utcfromtimestamp(
                int(rec['finish_current'])).strftime(DATE_FORMAT)
        else:
            if 'finish_prev' in rec:
                last_event_time = datetime.utcfromtimestamp(
                    int(rec['finish_prev'])).strftime(DATE_FORMAT)
            else:
                last_event_time = ''

        if 'start_current' in rec:
            event_time = datetime.utcfromtimestamp(
                int(rec['finish_current'])).strftime(DATE_FORMAT)
        else:
            event_time = last_event_time

        if event_type == "completed":
            if oldest_completed_target == '':
                oldest_completed_target = event_time
            if event_time < oldest_completed_target:
                oldest_completed_target = event_time

        descr = docs.get(key, '')
        event_duration = rec.get("timing_sec", 0)
        
        if last_event_time =='':
            last_event_time = None

        status.append(
            {"targetName": key,
             "targetDescription": descr,
             "targetType": event_type,
             "targetTime": event_time,
             "targetDuration": event_duration,
             "lastTargetCompletionTime": last_event_time,
             "targetLog": rec["log"]
             }
        )

    for target in not_started_targets:
        status.append({
            "targetName": target,
            "targetDescription": docs.get(target, ''),
            "targetType": "never started"
        })

    if n_in_progress > 0:
        current_status = 'Up and Running'
    else:
        current_status = 'Idle'

    pipeline = {
        "numberOfProgress": n_in_progress,
        "numberOfTargetsCompleted": n_total,
        "numberOfTargetsFailed": n_failed,
        "oldestCompletionTime": oldest_completed_target,
        "presentStatus": current_status
    }

    status_list["pipeline"] = pipeline
    status_list["status"] = status

    fo.write(json.dumps(status_list))


    fo.close()
