module.exports = {
    apps: [
        {
            name: "Strip Checker",
            script: "./strip_check.py",
            exp_backoff_restart_delay: 5000,
            interpreter: "/home/lejak/misc_fetcher/venv/bin/python3",
        },
        {
            name: "Strip Checker Bot",
            script: "./bot.py",
            exp_backoff_restart_delay: 5000,
            interpreter: "/home/lejak/misc_fetcher/venv/bin/python3",
            cwd: "/home/lejak/misc_fetcher/discord/",
        },
    ],
};
