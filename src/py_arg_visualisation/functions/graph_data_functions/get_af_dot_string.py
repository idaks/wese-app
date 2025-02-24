import pathlib
from collections import defaultdict
import clingo
import time

from py_arg_visualisation.functions.graph_data_functions.get_color import get_color

PATH_TO_ENCODINGS = pathlib.Path(__file__).parent / "encodings"


def generate_plain_dot_string(argumentation_framework, layout=any):
    dot_string = "digraph {\n"
    dot_string += 'node [fontname = "helvetica" , shape=circle, fixedsize=true, width=0.8, height=0.8] \n  edge [fontname = "helvetica"] \n rankdir={}  // Node defaults can be set here if needed\n'.format(
        "BT"
    )

    # Adding node information
    for argument in argumentation_framework.arguments:
        dot_string += f'    "{argument.name}" [fontsize=14]\n'

    # Adding edge information
    dot_string += f"    edge[labeldistance=1.5 fontsize=12]\n"
    for attack in argumentation_framework.defeats:
        dot_string += f'    "{attack.from_argument}" -> "{attack.to_argument}"\n'
    dot_string += "}"
    return dot_string


def extract_node_positions(layout_file):
    """
    Reads a layout.txt file and extracts node positions.

    Args:
        layout_file (str): Path to the layout file.

    Returns:
        dict: A dictionary mapping node names to (x, y) positions.
    """
    node_positions = {}

    try:
        with open(layout_file, "r") as f:
            lines = f.readlines()

        for line in lines:
            parts = line.split()
            if parts and parts[0] == "node":
                node_id = parts[1]  # Node name
                x, y = float(parts[2]), float(parts[3])  # Extract x, y coordinates
                node_positions[node_id] = (x, y)

    except FileNotFoundError:
        print(f"Warning: Layout file {layout_file} not found. Using default positions.")
    except Exception as e:
        print(f"Error reading layout file {layout_file}: {e}")

    return node_positions


def generate_dot_string(
    argumentation_framework,
    selected_arguments,
    color_blind_mode=False,
    layout=any,
    rank=any,
    special_handling=any,
    layout_freeze=False,
    layout_file=None,
):
    gr_status_by_arg, number_by_argument = get_numbered_grounded_extension(
        argumentation_framework
    )
    # processing the layout file
    layout_file = (
        pathlib.Path(__file__).parent.parent.parent.parent.parent
        / "temp"
        / "layout.txt"
    )
    node_positions = extract_node_positions(layout_file) if layout_file else {}
    # print(node_positions)

    if layout_freeze:
        graph_layout = "graph[layout=neato overlap=false]"
    else:
        graph_layout = "layout=dot"

    # creating the dot string
    dot_string = f"digraph {{\n{graph_layout} \n"
    dot_string += 'node [fontname = "helvetica"  shape=circle fixedsize=true width=0.8, height=0.8] \n  edge [fontname = "helvetica"] \n rankdir={}  // Node defaults can be set here if needed\n'.format(
        layout
    )

    # Adding node information
    is_extension_representation = False
    argument_extension_state = {}
    # undefined_arguments = []
    unselected_arguments = {arg.name for arg in argumentation_framework.arguments}
    for color, arguments in selected_arguments.items():
        if color in ["green", "red", "yellow"]:
            is_extension_representation = True
        if color == "green":
            status = "accepted"
        elif color == "red":
            status = "defeated"
        elif color == "yellow":
            status = "undefined"
            # if len(arguments)!=0:
            #     undefined_arguments=arguments
        else:
            status = "other"
        for argument_name in arguments:
            if argument_name != "":
                number = number_by_argument[argument_name]
                argument_extension_state[argument_name] = status
                if gr_status_by_arg[argument_name] == "undefined" and status in [
                    "accepted",
                    "defeated",
                ]:
                    argument_color = get_color(f"light-{color}", color_blind_mode)
                else:
                    argument_color = get_color(color, color_blind_mode)
                if is_extension_representation:
                    argument_label = f"{argument_name}.{number}"
                else:
                    argument_label = argument_name

                pos_attr = (
                    f'pos="{node_positions[argument_name][0]},{node_positions[argument_name][1]}!"'
                    if argument_name in node_positions and layout_freeze
                    else ""
                )
                node = (
                    f'    "{argument_name}" [style="filled" '
                    f'fillcolor="{argument_color}" '
                    f'label="{argument_label}" '
                    f"fontsize=14 {pos_attr}]\n"
                )
                dot_string += node

                unselected_arguments.remove(argument_name)
    for argument_name in unselected_arguments:
        dot_string += f'    "{argument_name}" [fontsize=14]\n'

    # Adding edge information
    dot_string += f"    edge[labeldistance=1.5 fontsize=12]\n"
    for attack in argumentation_framework.defeats:
        if is_extension_representation:
            from_argument_grounded_state = gr_status_by_arg[attack.from_argument.name]
            to_argument_grounded_state = gr_status_by_arg[attack.to_argument.name]
            from_argument_extension_state = argument_extension_state[
                attack.from_argument.name
            ]
            to_argument_extension_state = argument_extension_state[
                attack.to_argument.name
            ]
            from_argument_number = number_by_argument[attack.from_argument.name]
            to_argument_number = number_by_argument[attack.to_argument.name]

            # cal the against wind
            against_wind = False
            from_num = (
                float("inf")
                if from_argument_number == "∞"
                else int(from_argument_number)
            )
            to_num = (
                float("inf") if to_argument_number == "∞" else int(to_argument_number)
            )
            against_wind = from_num == float("inf") and to_num != float("inf")
            against_wind = against_wind or (from_num > to_num)

            if from_num == float("inf"):
                label = "∞"
            else:
                label = str(from_num + 1)

            # set initial style
            style = "solid"
            arrow_style = "vee"
            constraint_value = ""
            full_color = get_color("black", color_blind_mode)
            # handle grounded extensions
            # Accepted -> Defeated
            if (
                from_argument_grounded_state == "accepted"
                and to_argument_grounded_state == "defeated"
            ):
                full_color = get_color("green", color_blind_mode)
            # Defeated -> Accepted
            elif (
                from_argument_grounded_state == "defeated"
                and to_argument_grounded_state == "accepted"
            ):
                full_color = get_color("red", color_blind_mode)
            else:
                # handle the stable extensions
                # Stable Accepted -> Defeated (Grounded Undefined)
                if (
                    from_argument_extension_state == "accepted"
                    and to_argument_extension_state == "defeated"
                ):
                    extension_edge_color = get_color("green", color_blind_mode)
                    full_color = f"{extension_edge_color}"
                    label = ""
                # Stable Defeated -> Accepted(Grounded Undefined)
                elif (
                    from_argument_extension_state == "defeated"
                    and to_argument_extension_state == "accepted"
                ):
                    extension_edge_color = get_color("red", color_blind_mode)
                    full_color = f"{extension_edge_color}"
                    label = ""
                # Undefined -> Undefined
                elif (
                    from_argument_extension_state == "undefined"
                    and to_argument_extension_state == "undefined"
                ):
                    full_color = get_color("dark-yellow", color_blind_mode)
                # Undefined -> Defeated
                elif (
                    from_argument_extension_state == "undefined"
                    and to_argument_extension_state == "defeated"
                ):
                    full_color = get_color("gray", color_blind_mode)
                    style = "dotted"
                    arrow_style = "onormal"
                    constraint_value = set_constraint_con(special_handling, "BU")
                    label = ""
                # Defeated -> Undefined
                elif (
                    from_argument_extension_state == "defeated"
                    and to_argument_extension_state == "undefined"
                ):
                    full_color = get_color("gray", color_blind_mode)
                    style = "dotted"
                    arrow_style = "onormal"
                    constraint_value = set_constraint_con(special_handling, "BU")
                    label = ""
                # Defeated -> Defeated
                elif (
                    from_argument_extension_state == "defeated"
                    and from_argument_extension_state == "defeated"
                ):
                    full_color = get_color("gray", color_blind_mode)
                    style = "dotted"
                    arrow_style = "onormal"
                    constraint_value = set_constraint_con(special_handling, "BU")
                    label = ""

            if against_wind:
                if style == "dotted":
                    pass
                elif style == "invis":
                    pass
                else:
                    style = "dashed"
                constraint_value = set_constraint_con(special_handling, "RD")
                edge = (
                    f'"{attack.to_argument.name}" -> '
                    f'"{attack.from_argument.name}" '
                    f"[dir=back "
                    f'color="{full_color}" '
                    f'style= "{style}"'
                    f"{constraint_value}"
                    f'fontcolor="{full_color}"'
                    f'arrowtail="{arrow_style}"'
                    f'arrowhead="{arrow_style}"'
                    f'headlabel="{label}"]\n'
                )
            else:
                edge = (
                    f'"{attack.from_argument.name}" -> '
                    f'"{attack.to_argument.name}" '
                    f'[color="{full_color}" '
                    f'style="{style}"'
                    f"{constraint_value}"
                    f'fontcolor="{full_color}"'
                    f'arrowtail="{arrow_style}"'
                    f'arrowhead="{arrow_style}"'
                    f'taillabel="{label}"]\n'
                )
        else:
            edge = f'"{attack.from_argument.name}" -> "{attack.to_argument.name}"\n'
        dot_string += "    " + edge

    # Enable Ranks
    number_by_argument = {k: v for k, v in number_by_argument.items() if v != "∞"}
    if rank == "NR":
        pass
    elif rank == "AR":
        # in case we need the rank = max
        # max_value = max(number_by_argument.values())
        filtered_arguments = {k: v for k, v in number_by_argument.items()}
        nodes_by_value = defaultdict(list)
        for node, value in filtered_arguments.items():
            nodes_by_value[value].append(node)
        for value in sorted(nodes_by_value.keys()):
            nodes = nodes_by_value[value]
            if len(nodes) == 1:
                same_rank_string = f"// {{rank = same {' '.join(nodes)}}}"
            else:
                same_rank_string = f"{{rank = same {' '.join(nodes)}}}"
            dot_string += f"    {same_rank_string}\n"
    elif rank == "MR":
        min_state_nodes = [
            node
            for node, value in number_by_argument.items()
            if value == min(number_by_argument.values())
        ]
        min_rank_string = f"{{rank = min {' '.join(min_state_nodes)}}}"
        dot_string += f"    {min_rank_string}\n"

    dot_string += "}"
    # print(dot_string)
    return dot_string


def get_numbered_grounded_extension(argumentation_framework):
    # Keep argument ID dictionary.
    argument_name_to_id = {}
    id_to_argument_name = {}
    for arg_id, argument in enumerate(argumentation_framework.arguments):
        argument_name_to_id[argument.name] = "a" + str(arg_id)
        id_to_argument_name["a" + str(arg_id)] = argument.name

    # Run clingo solver.
    ctl = clingo.Control()
    ctl.load(str(PATH_TO_ENCODINGS / "grounded_encoding.dl"))
    for argument in argumentation_framework.arguments:
        pos_fact = f"pos({argument_name_to_id[argument.name]})."
        ctl.add("base", [], pos_fact)
    for defeat in argumentation_framework.defeats:
        ctl.add(
            "base",
            [],
            f"attack({argument_name_to_id[defeat.from_argument.name]}, "
            f"{argument_name_to_id[defeat.to_argument.name]}).",
        )
    ctl.ground([("base", [])])
    models = []
    ctl.solve(on_model=lambda m: models.append(m.symbols(shown=True)))

    # Read output of clingo solver.
    atoms = models[0]
    number_by_argument = {}
    status_by_argument = {}
    for atom in atoms:
        if atom.name == "len":
            argument_name = id_to_argument_name[atom.arguments[1].name]
            if atom.arguments[0].name == "undefined":
                number_by_argument[argument_name] = "∞"
            else:
                number_by_argument[argument_name] = str(atom.arguments[2])
            status_by_argument[argument_name] = atom.arguments[0].name
    return status_by_argument, number_by_argument


def set_style(keyword, style, rm_edge):
    if rm_edge != None and keyword in rm_edge:
        return "invis"
    else:
        return style


def set_constraint_con(bool, con_type):
    if not bool:
        return 'constraint="false"'
    if con_type == "BU" and "BU" not in bool:
        return 'constraint="false"'
    elif con_type == "RD" and "RD" not in bool:
        return 'constraint="false"'
    else:
        return ""
