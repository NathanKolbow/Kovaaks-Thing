import PySimpleGUI as sg
import os
import sys
from pathlib import Path
from datetime import datetime
import globals


CHALLENGE_DATA = {}
UNIQUE_CHALLENGES = []
WINDOW = None
DRAW_TEXT = True
MAX_STATUS = True


def main():
    global WINDOW
    global CHALLENGE_DATA
    global UNIQUE_CHALLENGES
    global DRAW_TEXT
    global MAX_STATUS

    # default_path = Path(os.environ["ProgramFiles(x86)"], "Steam")
    default_path = Path("M:\\SteamLibrary\\")

    stats_path = try_resolve_kovaaks(str(default_path))
    if stats_path is not None:
        pass
    else:
        layout = sg.Column([
            [
                sg.Text("Your Steam library path could not be located "
                        + "automatically.")
            ],
            [
                sg.Text("Steam Library Path:"),
                sg.InputText(default_text=default_path,
                             key="Kovaaks-Location-Input", enable_events=True),
                sg.FolderBrowse(key="Folder-Browser", enable_events=True),
            ]
        ], element_justification='center')

        WINDOW = sg.Window("Library Locator", [[layout]])
        WINDOW.Finalize()

        while True:
            event, val = WINDOW.read()

            if event == sg.WIN_CLOSED:
                WINDOW.close()
                sys.exit()
                break
            elif event == 'Kovaaks-Location-Input':
                stats_path = try_resolve_kovaaks(WINDOW['Kovaaks-Location-Input'].Get())
                if stats_path is not None:
                    break
                else:
                    print("None")

    stat_files = os.listdir(path=stats_path)

    # Collect stats from each file
    for file in stat_files:
        if ' - Challenge - ' in file:
            split = file.split(' - Challenge - ')
            if split[0] not in CHALLENGE_DATA:
                CHALLENGE_DATA[split[0]] = []
                UNIQUE_CHALLENGES.append(split[0])

            date = split[1].split(' Stats.csv')[0]
            full_list = date.split('-')[0].split('.') + date.split('-')[1].split('.')
            full_list = [int(item) for item in full_list]

            date = datetime(year=full_list[0], month=full_list[1], day=full_list[2],
                            hour=full_list[3], minute=full_list[4], second=full_list[5])
            dict = {}
            dict['_datetime'] = date.timestamp()
            dict.update(process_stats(Path(stats_path, file)))

            CHALLENGE_DATA[split[0]].append(dict)

    # Sort the dictionary entries by their datetime
    for k in CHALLENGE_DATA:
        CHALLENGE_DATA[k] = sorted(CHALLENGE_DATA[k], key=lambda i: i['_datetime'])

    print(CHALLENGE_DATA)

    # All of the info for every session is now in UNIQUE_CHALLENGES,
    # so now we build the window for viewing this info
    layout = [
        [
            sg.Combo(UNIQUE_CHALLENGES, key='Challenge-Selector',
                     default_value=UNIQUE_CHALLENGES[0], enable_events=True),
            sg.Button("Toggle Text", key='Text-Toggle'),
            sg.Button("Toggle Max", key='Max-Toggle')
        ],
        [
            # GRAPH_COORDS will probably have to be dynamic somehow at some point
            sg.Graph(globals.GRAPH_SIZE, globals.GRAPH_COORDS_BOTTOM_LEFT,
                     globals.GRAPH_COORDS_TOP_RIGHT, background_color='black',
                     key='Stats-Graph')
        ]
    ]
    WINDOW = sg.Window("Analysis", layout)
    WINDOW.Finalize()

    # Draw the first graph
    draw_stats(UNIQUE_CHALLENGES[0])

    while True:
        event, val = WINDOW.read()

        if event == sg.WIN_CLOSED:
            WINDOW.close()
            break
        elif event == 'Challenge-Selector':
            draw_stats(WINDOW['Challenge-Selector'].Get())
        elif event == 'Text-Toggle':
            DRAW_TEXT = not DRAW_TEXT
            draw_stats(WINDOW['Challenge-Selector'].Get())
        elif event == 'Max-Toggle':
            MAX_STATUS = not MAX_STATUS
            draw_stats(WINDOW['Challenge-Selector'].Get())


def draw_stats(challenge_name):
    # Currently only going to display score & accuracy
    global WINDOW
    global CHALLENGE_DATA
    global MAX_STATUS
    global DRAW_TEXT

    WINDOW['Stats-Graph'].Erase()

    list = CHALLENGE_DATA[challenge_name]
    temp = [x['general_data']['Score'] for x in list]
    max_score = max(temp)
    min_score = min(temp)
    diff_score = max_score - min_score if not max_score == min_score else 1

    step_size = 0 if len(list) == 1 else globals.GRAPH_BOUNDARIES[1][1] / (len(list) - 1)
    last_score_loc = (-1, -1)
    last_acc_loc = (-1, -1)
    for i in range(0, len(list)):
        score = list[i]['general_data']['Score']
        if MAX_STATUS:
            score_loc = (i * step_size, ((score-min_score)/(diff_score))
                         * globals.GRAPH_BOUNDARIES[1][1])
        else:
            score_loc = (i * step_size, (score/max_score) * globals.GRAPH_BOUNDARIES[1][1])
        WINDOW['Stats-Graph'].DrawPoint(score_loc, size=10, color='green')
        if DRAW_TEXT:
            WINDOW['Stats-Graph'].DrawText(str(round(score, 2)),
                                           (score_loc[0], score_loc[1] + 15), color='green')
        if last_score_loc != (-1, -1):
            WINDOW['Stats-Graph'].DrawLine(last_score_loc, score_loc, color='green', width=1)
        last_score_loc = score_loc

        acc = list[i]['general_data']['Accuracy']
        acc_loc = (i * step_size, acc * globals.GRAPH_BOUNDARIES[1][1])
        WINDOW['Stats-Graph'].DrawPoint(acc_loc, size=10, color='red')
        if DRAW_TEXT:
            WINDOW['Stats-Graph'].DrawText(str(round(acc*100, 2)),
                                           (acc_loc[0], acc_loc[1] + 15), color='red')
        if last_acc_loc != (-1, -1):
            WINDOW['Stats-Graph'].DrawLine(last_acc_loc, acc_loc, color='red', width=1)
        last_acc_loc = acc_loc


def process_stats(file):
    dict = {}

    with open(file, 'r') as f:
        # Category header
        kill_data_header = f.readline().split(',')
        dict['kill_data'] = {}
        for item in kill_data_header:
            dict['kill_data'][item] = []

        line = f.readline()
        while line != '\n':
            split = [conv(x) for x in line.split(',')]
            for i in range(0, len(split)):
                dict['kill_data'][kill_data_header[i]].append(split[i])

            line = f.readline()

        weapon_data_header = f.readline().split(',')
        dict['weapon_data'] = []
        split = f.readline().split(',')
        while split[0] != '\n':
            to_add = {}
            for i in range(0, len(split) - 1):
                to_add[weapon_data_header[i]] = conv(split[i])
            dict['weapon_data'].append(to_add)
            split = f.readline().split(',')

        dict['general_data'] = {}
        split = f.readline().split(',')
        while split[0] != '\n':
            dict['general_data'][split[0][:-1]] = conv(split[1])
            split = f.readline().split(',')

        # Compute overall accuracy
        shots = 0
        hits = 0
        for entry in dict['weapon_data']:
            shots += entry['Shots']
            hits += entry['Hits']
        dict['general_data']['Accuracy'] = hits/shots

        dict['settings'] = {}
        split = f.readline().split(',')
        while split[0] != '' and split[0] != '\n':
            dict['settings'][split[0][:-1]] = conv(split[1])
            split = f.readline().split(',')

    return dict


def conv(val):
    val = val.replace('\n', '')
    try:
        return int(val)
    except ValueError:
        try:
            return float(val)
        except ValueError:
            return val


def try_resolve_kovaaks(path):
    list = ["", "steamapps", "common", "FPSAimTrainer", "FPSAimTrainer", "stats"]
    last = -1
    for i in range(0, len(list)):
        if not list[i] in path:
            last = i
            break
    path = Path(path)

    if last == -1:
        pass
    elif last == 5:
        if str(path).count(list[3]) == 1:
            path = Path.joinpath(path, Path(list[4], list[5]))
        else:
            path = Path.joinpath(path, Path(list[5]))
    else:
        for i in range(last, len(list)):
            path = Path.joinpath(path, Path(list[i]))

    if path.exists():
        return path
    else:
        return None


if __name__ == '__main__':
    main()
