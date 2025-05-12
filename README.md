# Tow

Tow is an app for controlling UNH's tow carriage motion.

To run the app in dev mode, run:

```sh
make
```

To compile to an executable and create a shortcut, run:

```sh
make shortcut
```

This shortcut can be copied wherever you like, pinned to the taskbar, etc.

## Editing the UI

To edit the UI interactively with Qt Designer, call:

```sh
make edit-ui
```

After saving changes, compile the `mainwindow.ui` file to a Python module
with:

```sh
make ui
```
