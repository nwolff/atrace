from . import model


def collect_variable_list(trace: model.Trace) -> list[model.Variable]:
    variable_list = []
    for traceItem in trace:
        match traceItem.event:
            case model.VariableChangeEvent(variable_name, _):
                if variable_name not in variable_list:
                    variable_list.append(variable_name)
    return variable_list


def coalesce_print_events(trace: model.Trace) -> model.Trace:
    last_print_item = None
    for trace_item in trace:
        match trace_item.event:
            case model.PrintEvent(text):
                if (
                    last_print_item is None
                    or trace_item.line_no != last_print_item.line_no
                ):
                    last_print_item = trace_item
                else:
                    last_print_item.event.text += text
                    trace_item.event = None  # Mark for deletion
            case _:
                last_print_item = None

    return [item for item in trace if item.event is not None]


def contains_prints(trace: model.Trace) -> bool:
    for trace_item in trace:
        match trace_item.event:
            case model.PrintEvent(text):
                return True
    return False


def dump_report(trace: model.Trace) -> None:
    trace = coalesce_print_events(trace)

    variable_list = collect_variable_list(trace)
    print("vars:", variable_list)

    for trace_item in trace:
        print(trace_item.line_no, trace_item.event)
