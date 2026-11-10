"""Behavior checks using disposable task folders and installed hook commands."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1]
FILES = ("BRIEF.md", "STATE.md", "DECISIONS.md", "LOG.md")


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="longwork-test-")
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.task = self.root / "task"
        self.make_task(self.task)
        self.env = dict(os.environ, LONGWORK_GUARD_DIR=str(self.root / "store"))

    def make_task(self, task):
        task.mkdir()
        for name in FILES:
            (task / name).write_text(name + "\n")

    def run_guard(self, action, agent="claude", sid="session-1", path=None,
                  init=False, retry=False, env=None):
        args = ["bash", str(SOURCE / "guard.sh"), action, agent]
        if action in ("register", "off"):
            args.append(sid)
        if action == "register":
            if init:
                args.append("init")
            args.append(str(self.task if path is None else path))
        payload = {"session_id": sid, "stop_hook_active": retry}
        result = subprocess.run(args, input=json.dumps(payload), text=True,
                                capture_output=True, env=env or self.env)
        return result

    def ok(self, action, **kwargs):
        result = self.run_guard(action, **kwargs)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def block(self, **kwargs):
        response = json.loads(self.ok("check", **kwargs))
        self.assertEqual(response["decision"], "block")
        return response

    def test_unregistered_hooks_are_silent_and_create_nothing(self):
        for agent in ("claude", "codex"):
            for action in ("mark", "check"):
                self.assertEqual(self.ok(action, agent=agent), "")
        self.assertFalse((self.root / "store").exists())

    def test_resume_first_turn_is_checked(self):
        self.assertIn("on for", self.ok("register"))
        self.block()

    def test_normal_turn_update_passes(self):
        self.ok("register")
        self.ok("mark")
        with (self.task / "STATE.md").open("a") as stream:
            stream.write("Next: finish\n")
        self.assertEqual(self.ok("check"), "")

    def test_log_only_change_passes_mechanical_check(self):
        self.ok("register")
        (self.task / "LOG.md").write_text("A dated work record\n")
        self.assertEqual(self.ok("check"), "")

    def test_retry_checks_repair_then_next_turn_can_block(self):
        for agent in ("claude", "codex"):
            self.ok("register", agent=agent)
            self.block(agent=agent)
            self.ok("mark", agent=agent)  # Native continuation may submit a prompt.
            with (self.task / "LOG.md").open("a") as stream:
                stream.write(agent + " repair\n")
            self.assertEqual(self.ok("check", agent=agent, retry=True), "")
            self.ok("mark", agent=agent)
            self.block(agent=agent)

    def test_retry_without_repair_warns_even_if_native_flag_is_absent(self):
        self.ok("register", agent="codex")
        self.block(agent="codex")
        self.ok("mark", agent="codex")
        response = json.loads(self.ok("check", agent="codex"))
        self.assertNotIn("decision", response)
        self.assertIn("unresolved after continuation", response["systemMessage"])
        self.ok("mark", agent="codex")
        self.block(agent="codex")  # A subsequent user turn gets its own attempt.

    def test_native_retry_flag_avoids_additional_continuations(self):
        self.ok("register")
        response = json.loads(self.ok("check", retry=True))
        self.assertNotIn("decision", response)
        self.assertIn("unresolved", response["systemMessage"])

    def test_missing_records_reject_resume_and_block_active_task(self):
        (self.task / "STATE.md").unlink()
        result = self.run_guard("register")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("on for", result.stdout)
        self.assertFalse((self.root / "store").exists())
        (self.task / "STATE.md").write_text("state\n")
        self.ok("register")
        (self.task / "LOG.md").unlink()
        self.ok("mark")
        self.assertIn("missing or unreadable", self.block()["reason"])

    def test_missing_task_directory_blocks(self):
        self.ok("register")
        for name in FILES:
            (self.task / name).unlink()
        self.task.rmdir()
        self.assertIn("directory is unavailable", self.block()["reason"])

    def test_init_interview_then_record_creation_then_enforcement(self):
        task = self.root / "new-task"
        self.assertIn("pending initialization", self.ok("register", path=task, init=True))
        for _ in range(2):
            self.ok("mark")
            self.assertEqual(self.ok("check"), "")
        for name in FILES[:-1]:
            (task / name).write_text(name)
        self.assertEqual(self.ok("check"), "")
        (task / "LOG.md").write_text("Init recorded\n")
        self.assertEqual(self.ok("check"), "")
        self.ok("mark")
        self.block()

    def test_init_on_existing_complete_task_is_immediately_active(self):
        self.assertIn("on for", self.ok("register", init=True))
        self.block()

    def test_paths_preserve_quotes_spaces_and_shell_metacharacters(self):
        task = self.root / "task's \"quoted\" `name` $(untouched) folder"
        self.make_task(task)
        self.assertIn(str(task), self.ok("register", path=task))
        self.block()
        (task / "LOG.md").write_text("updated\n")
        self.assertEqual(self.ok("check"), "")

    def test_file_boundaries_are_part_of_fingerprint(self):
        (self.task / "BRIEF.md").write_text("abc")
        (self.task / "STATE.md").write_text("def")
        self.ok("register")
        (self.task / "BRIEF.md").write_text("abcd")
        (self.task / "STATE.md").write_text("ef")
        self.assertEqual(self.ok("check"), "")

    def test_registration_storage_failure_never_reports_on(self):
        bad_store = self.root / "blocked"
        bad_store.write_text("not a directory")
        env = dict(self.env, LONGWORK_GUARD_DIR=str(bad_store))
        result = self.run_guard("register", env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("on for", result.stdout)
        state_dir = self.root / "directory-store" / "claude" / "session-1.json"
        state_dir.mkdir(parents=True)
        env = dict(self.env, LONGWORK_GUARD_DIR=str(self.root / "directory-store"))
        result = self.run_guard("register", env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("on for", result.stdout)

    def test_bad_session_id_cannot_escape_store(self):
        result = self.run_guard("register", sid="../outside")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "store").exists())

    def test_agents_and_sessions_do_not_share_bindings(self):
        other = self.root / "other"
        self.make_task(other)
        self.ok("register", agent="claude")
        self.ok("register", agent="codex", path=other)
        self.ok("register", sid="session-2", path=other)
        (other / "LOG.md").write_text("Other session updated\n")
        self.assertEqual(self.ok("check", agent="codex"), "")
        self.assertEqual(self.ok("check", sid="session-2"), "")
        self.block(agent="claude")
        self.ok("off", agent="codex")
        self.assertEqual(self.ok("check", agent="codex"), "")
        self.assertIn("systemMessage", json.loads(self.ok("check", agent="claude")))

    def test_off_and_reactivation(self):
        self.ok("register")
        self.ok("off")
        self.assertEqual(self.ok("mark"), "")
        self.assertEqual(self.ok("check"), "")
        self.ok("register")
        self.block()

    def test_corrupt_state_is_reported(self):
        self.ok("register")
        (self.root / "store" / "claude" / "session-1.json").write_text("broken")
        result = self.run_guard("check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid guard state", result.stderr)

    def test_linked_skill_folder_and_hook_commands(self):
        home = self.root / "home with spaces"
        for skills in (home / ".claude" / "skills", home / ".agents" / "skills"):
            skills.mkdir(parents=True)
            (skills / "longwork").symlink_to(SOURCE)
            for name in ("SKILL.md", "WORKFLOW.md", "guard.sh", "templates",
                         "agents/openai.yaml"):
                self.assertTrue((skills / "longwork" / name).exists(), name)
        env = dict(self.env, HOME=str(home))
        frontmatter = (SOURCE / "SKILL.md").read_text().split("---")[1]
        claude = dict(re.findall(r"^  (\w+):\n(?:.*\n)*?\s+command: '(.+)'$",
                                 frontmatter, re.M))
        codex = {event: groups[0]["hooks"][0]["command"] for event, groups in
                 json.loads((SOURCE / "codex" / "hooks.json").read_text())["hooks"].items()}
        for agent, commands in (("claude", claude), ("codex", codex)):
            self.assertEqual(set(commands), {"UserPromptSubmit", "Stop"})
            self.assertTrue(all(f" {agent}" in c for c in commands.values()))
            self.check_hook_commands(agent, commands, env)

    def check_hook_commands(self, agent, hooks, env):
        self.ok("register", agent=agent, env=env)
        for event, decision in (("UserPromptSubmit", False), ("Stop", True)):
            command = hooks[event]
            result = subprocess.run(["bash", "-c", command], input=json.dumps({
                "session_id": "session-1", "turn_id": "native-shaped-turn",
                "hook_event_name": event, "stop_hook_active": False,
            }), env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            if decision:
                self.assertEqual(json.loads(result.stdout)["decision"], "block")
            else:
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
