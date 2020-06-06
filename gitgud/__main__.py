import os
import sys
import webbrowser

import argparse

from git import Repo
from git.exc import InvalidGitRepositoryError

import gitgud
from gitgud.operations import get_operator
from gitgud.operations import Operator
from gitgud.skills import all_skills
from gitgud.skills.user_messages import all_levels_complete
from gitgud.skills.user_messages import show_tree
from gitgud.hooks import all_hooks


class InitializationError(Exception):
    pass


class GitGud:
    def __init__(self):
        # Only gets operator if Git Gud has been initialized
        self.file_operator = get_operator()

        self.parser = argparse.ArgumentParser(prog='git gud')
        self.parser.add_argument(
                '--version',
                action='version',
                version='%(prog)s ' + gitgud.__version__)

        load_description = '\n'.join([
            "Load a specific skill or level. This command can be used in several ways.",  # noqa: E501
            "\n",
            "============Basic Usage============",
            "\n",
            "These commands are the simplest commands to load a level on a certain skill, and are identical in functionality:",  # noqa: E501
            "\n",
            "   git gud load <skill> <level>",
            "   git gud load <skill>-<level>",
            "\n",
            "<skill> and <level> could either be the name of the skill/level or the number of the skill/level.",  # noqa: E501
            "Running `git gud skills` will help you find the number and name associated with each skill/level.",  # noqa: E501
            "\n",
            "Here are example uses which load the same level:",
            "\n",
            "   git gud load basics-2",
            "   git gud load 1 branching",
            "\n",
            "============Additional Commands============",
            "\n",
            "`git gud load` supports additional shortcut commands to ease level navigation.",  # noqa: E501
            "\n",
            "======Loading the first level on a skill======",
            "\n",
            "This command loads the first level on the specified skill:",
            "\n",
            "   git gud load <skill>",
            "\n",
            "======Loading a level on the current skill======",
            "\n",
            "This command loads the specified level of the current skill.",
            "NOTE: <level> MUST be a number in order for this command to work.",  # noqa: E501
            "\n",
            "   git gud load -<level>",
            "\n",
        ])

        show_description = "".join([
            "Helper command to show certain information.",
            "\n\n",
            "Subcommands:",
            "\n",
            "  <command>",
            "\n",
            "    tree", "\t", "Show the current state of the branching tree"
        ])

        self.subparsers = self.parser.add_subparsers(
                title='Subcommands',
                metavar='<command>',
                dest='command'
        )

        self.subparsers.add_parser(
                'status',
                help='Print out the name of the current level',
                description='Print out the name of the current level')
        self.subparsers.add_parser(
                'instructions',
                help='Show the instructions for the current level',
                description='Show the instructions for the current level')
        self.subparsers.add_parser(
                'goal',
                help='Concisely show what needs to be done to complete the level.',  # noqa: E501
                description='Concisely show what needs to be done to complete the level.')  # noqa: E501
        self.subparsers.add_parser(
                'reset',
                help='Reset the current level',
                description='Reset the current level')
        self.subparsers.add_parser(
                'reload',
                help='Alias for reset',
                description='Reset the current level. Reload command is an alias for reset command.')  # noqa: E501
        self.subparsers.add_parser(
                'test',
                help="Test to see if you've successfully completed the current level",  # noqa: E501
                description="Test to see if you've successfully completed the current level")  # noqa: E501
        self.subparsers.add_parser(
                'skills',
                help='List skills',
                description='List skills')
        self.subparsers.add_parser(
                'goal',
                help='Show a description of the current goal',
                description='Show a description of the current goal')
        self.subparsers.add_parser(
                'contributors',
                help='Show project contributors webpage',
                description='Show all the contributors of the project')
        self.subparsers.add_parser(
                'issues',
                help='Show project issues webpage',
                description="Show all the issues for the project")

        help_parser = self.subparsers.add_parser(
                'help',
                help='Show help for commands',
                description='Show help for commands'
        )
        help_parser.add_argument(
                'command_name',
                metavar='cmd',
                help="Command to get help on", nargs='?'
        )

        init_parser = self.subparsers.add_parser(
                'init',
                help='Init Git Gud and load first level',
                description='Initialize the direcotry with a git repository and load the first level of Git Gud.'  # noqa: E501
        )
        init_parser.add_argument('--force', action='store_true')

        load_parser = self.subparsers.add_parser(
                'load',
                help='Load a specific skill or level',
                description=load_description,
                formatter_class=argparse.RawDescriptionHelpFormatter)
        load_parser.add_argument(
                'skill_name',
                metavar='skill',
                help='Skill to load')
        load_parser.add_argument(
                'level_name',
                metavar='level',
                nargs='?',
                help='Level to load')

        levels_parser = self.subparsers.add_parser(
                'levels',
                help='List levels in a skill',
                description='List the levels in the specified skill or in the current skill if Git Gud has been initialized and no skill is provided. To see levels in all skills, use `git gud skills`.')  # noqa: E501
        levels_parser.add_argument('skill_name', metavar='skill', nargs='?')

        commit_parser = self.subparsers.add_parser(
                'commit',
                help='Quickly create and commit a file',
                description='Quickly create and commit a file')
        commit_parser.add_argument('file', nargs='?')

        show_parser = self.subparsers.add_parser(
                'show',
                description=show_description,
                formatter_class=argparse.RawDescriptionHelpFormatter)
        show_parser.add_argument(
                'cmd',
                metavar='cmd',
                help='Command to show information',
                nargs='?')

        self.command_dict = {
            'help': self.handle_help,
            'init': self.handle_init,
            'status': self.handle_status,
            'instructions': self.handle_instructions,
            'goal': self.handle_goal,
            'reset': self.handle_reset,
            'reload': self.handle_reset,
            'test': self.handle_test,
            'skills': self.handle_skills,
            'levels': self.handle_levels,
            'load': self.handle_load,
            'commit': self.handle_commit,
            'show-tree': self.handle_show_tree,
            'show': self.handle_show,
            'contributors': self.handle_contrib,
            'issues': self.handle_issues
        }

    def is_initialized(self):
        return self.file_operator is not None

    def assert_initialized(self, skip_level_check=False):
        if not self.is_initialized():
            raise InitializationError(
                    'Git gud has not been initialized. Use "git gud init" to initialize')  # noqa: E501

        if not skip_level_check:
            try:
                self.file_operator.get_level()
            except KeyError:
                level_name = self.file_operator.read_level_file()
                raise InitializationError(
                        'Currently loaded level does not exist: "{}"'
                        .format(level_name))

    def handle_help(self, args):
        if args.command_name is None:
            self.parser.print_help()
        else:
            try:
                self.subparsers.choices[args.command_name].print_help()
            except KeyError:
                print('No such command exists: "{}"'
                      .format(args.command_name))
                print()
                self.parser.print_help()

    def handle_init(self, args):
        # Make sure it's safe to initialize
        if not args.force:
            # We aren't forcing
            if self.file_operator:
                print('Repo {} already initialized for git gud.'
                      .format(self.file_operator.path))
                print('Use --force to initialize {}.'.format(os.getcwd()))
                return

            self.file_operator = Operator(os.getcwd(), initialize_repo=False)

            if os.path.exists(self.file_operator.git_path):
                # Current directory is a git repo
                print('Currently in a git repo. Use --force to force initialize here.')  # noqa: E501
                return
            if os.path.exists(self.file_operator.gg_path):
                # Current directory is a git repo
                print('Git gud has already initialized. Use --force to force initialize again.')  # noqa: E501
                return
            if len(os.listdir(self.file_operator.path)) != 0:
                print('Current directory is nonempty. Use --force to force initialize here.')  # noqa: E501
                return
        else:
            print('Force initializing git gud.')
            if not self.file_operator:
                self.file_operator = Operator(
                        os.getcwd(),
                        initialize_repo=False)

        # After here, we initialize everything
        try:
            self.file_operator.repo = Repo(self.file_operator.path)
        except InvalidGitRepositoryError:
            self.file_operator.repo = Repo.init(self.file_operator.path)

        if not os.path.exists(self.file_operator.gg_path):
            os.mkdir(self.file_operator.gg_path)

        # Git uses unix-like path separators
        python_exec = sys.executable.replace('\\', '/')

        for git_hook_name, module_hook_name, accepts_args in all_hooks:
            path = os.path.join(self.file_operator.hooks_path, git_hook_name)
            if accepts_args:
                forward_stdin = 'cat - |'
                passargs = ' "$@"'
            else:
                forward_stdin = ''
                passargs = ''

            with open(path, 'w+') as hook_file:
                hook_file.write('#!/bin/bash' + os.linesep)
                hook_file.write(
                        forward_stdin +
                        python_exec + ' -m gitgud.hooks.' + module_hook_name +
                        passargs + os.linesep)
                hook_file.write(
                    "if [[ $? -ne 0 ]]" + os.linesep + ""
                    "then" + os.linesep + ""
                    "\t exit 1" + os.linesep + ""
                    "fi" + os.linesep)

            # Make the files executable
            mode = os.stat(path).st_mode
            mode |= (mode & 0o444) >> 2
            os.chmod(path, mode)

        all_skills["0"]["1"].setup(self.file_operator)

    def handle_status(self, args):
        if self.is_initialized():
            try:
                level = self.file_operator.get_level()
                level.status()
            except KeyError:
                level_name = self.file_operator.read_level_file()
                print('Currently on unregistered level: "{}"'
                      .format(level_name))
        else:
            print("Git gud not initialized.")
            print('Initialize using "git gud init"')

    def handle_instructions(self, args):
        self.assert_initialized()
        self.file_operator.get_level().instructions()

    def handle_goal(self, args):
        self.assert_initialized()
        self.file_operator.get_level().goal()

    def handle_reset(self, args):
        self.assert_initialized()

        level = self.file_operator.get_level()
        level.setup(self.file_operator)

    def handle_test(self, args):
        self.assert_initialized()
        level = self.file_operator.get_level()
        level.test(self.file_operator)

    def handle_skills(self, args):
        if self.is_initialized():
            try:
                cur_skill = self.file_operator.get_level().skill
                print('Currently on skill: "{}"'.format(cur_skill.name))
                print()
            except KeyError:
                pass

        # Add two for quotes
        skill_formatted_len = max(len(skill.name) for skill in all_skills) + 2

        skill_format_template = 'Skill ' \
            '{skill_number} - {formatted_skill_name} : ' \
            '{num_levels:>2} level{plural}'
        level_format_template = "    Level {:>2} : {:<3}"

        for skill_number, skill in enumerate(all_skills):
            # TODO Add description
            print(skill_format_template.format(
                skill_number=skill_number,
                formatted_skill_name='"{}"'
                .format(skill.name).ljust(skill_formatted_len),
                num_levels=len(skill),
                plural="s" if len(skill) > 1 else ""
            ))

            for index, level in enumerate(skill):
                print(level_format_template.format(index + 1, level.name))

        print("\nLoad a level with `git gud load`")

    def handle_levels(self, args):
        key_error_flag = False
        if args.skill_name is None:
            if self.file_operator is None:
                self.subparsers.choices['levels'].print_help()
                return
            try:
                skill = self.file_operator.get_level().skill
            except KeyError:
                skill_name = self.file_operator.read_level_file().split()[0]
                print('Cannot find any levels in skill: "{}"'.format(skill_name))  # noqa: E501
                return
        else:
            try:
                skill = all_skills[args.skill_name]
            except KeyError:
                print('There is no skill "{}".'.format(args.skill_name))
                print('You may run "git gud skills" to print all the skills. \n')  # noqa: E501
                skill = self.file_operator.get_level().skill
                key_error_flag = True

        if key_error_flag or args.skill_name is None:
            print('Levels in the current skill "{}" : \n'.format(skill.name))
        else:
            print('Levels for skill "{}" : \n'.format(skill.name))

        for index, level in enumerate(skill):
            print(str(index + 1) + ": " + level.name)

        print('\nTo see levels in all skills, run "git gud skills".')

    def handle_load(self, args):
        self.assert_initialized(skip_level_check=True)

        # Check if we're just going forward or back
        if args.skill_name.lower() in {"next", "prev", "previous"}:
            query = args.skill_name.lower()
            level = self.file_operator.get_level()

            if query == "next":
                level_to_load = level.next_level
            else:
                query = "previous"
                level_to_load = level.prev_level

            if level_to_load is not None:
                level_to_load.setup(self.file_operator)
            else:
                if query == "next":
                    all_levels_complete()
                else:
                    print('Already on the first level. To reload the level, use "git gud reload".')  # noqa: E501
                print('\nTo view levels/skills, use "git gud levels" or "git gud skills"')  # noqa: E501
            return

        # Set up args.level_name and args.skill_name
        if args.level_name:
            if args.skill_name == "-":
                # Replace the dash with the current skill's name.
                args.skill_name = self.file_operator.get_level().skill.name
        else:
            skill_and_level = args.skill_name.split("-", 1)
            if len(skill_and_level) == 2:
                args.skill_name, args.level_name = tuple(skill_and_level)
            else:
                args.skill_name = skill_and_level[0]
                args.level_name = '1'

        if not args.skill_name:
            args.skill_name = self.file_operator.get_level().skill.name

        if args.skill_name in all_skills.keys():
            skill = all_skills[args.skill_name]
            if args.level_name in skill.keys():
                level = skill[args.level_name]
                level.setup(self.file_operator)
            else:
                print('Level "{}" does not exist'.format(args.level_name))
                print('To view levels/skills, use "git gud levels" or "git gud skills"\n')  # noqa: E501
        else:
            print('Skill "{}" does not exist'.format(args.skill_name))
            print('To view levels/skills, use "git gud levels" or "git gud skills"\n')  # noqa: E501

    def handle_commit(self, args):
        self.assert_initialized()

        last_commit = self.file_operator.get_last_commit()
        commit_name = str(int(last_commit) + 1)

        if args.file is not None:
            try:
                int(args.file)
                commit_name = args.file
            except ValueError:
                pass

        print('Simulating: Create file "{}"'.format(commit_name))
        print('Simulating: git add {}'.format(commit_name))
        print('Simulating: git commit -m "{}"'.format(commit_name))

        commit = self.file_operator.add_and_commit(commit_name)
        print("New Commit: {}".format(commit.hexsha[:7]))
        self.file_operator.track_commit(commit_name, commit.hexsha)

        # Next "git gud commit" name
        if int(commit_name) > int(last_commit):
            self.file_operator.write_last_commit(commit_name)

    def handle_show(self, args):
        if args.cmd == "tree":
            show_tree()
        else:
            print('Error: `git gud show` takes specific arguments. Type `git gud help show` for more information.')  # noqa: E501

    def handle_show_tree(self, args):
        show_tree()

    def handle_contrib(self, args):
        contrib_website = "https://github.com/benthayer/git-gud/graphs/" \
            "contributors"
        webbrowser.open_new(contrib_website)

    def handle_issues(self, args):
        issues_website = "https://github.com/benthayer/git-gud/issues"
        webbrowser.open_new(issues_website)

    def parse(self):
        args, _ = self.parser.parse_known_args()
        if args.command is None:
            if not self.is_initialized():
                print('Currently in an uninitialized directory.')
                print('Get started by running "git gud init" in a new directory!')  # noqa: E501
            else:
                self.parser.print_help()
        else:
            try:
                self.command_dict[args.command](args)
            except InitializationError as error:
                print(error)


def main():
    GitGud().parse()


if __name__ == '__main__':
    main()
