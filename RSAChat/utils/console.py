import cmd
import inspect
import traceback
from . import general
from . import cmdargparse
from . import ansi


class Command(general.MethodDecorator):
    def initParametric(self, docstring):
        self._argSpec = inspect.getfullargspec(self.function)
        self._argCount = len(self._argSpec.args) - 1
        self._necessaryCount = self._argCount - (len(self._argSpec.defaults) if self._argSpec.defaults else 0)
        self._hasVarArgs = self._argSpec.varargs is not None
        lDesc = docstring + ("\n" + self.getAnnoDescs() if self._argSpec.annotations else "")
        self._help = "Usage: {{}} {signature}\n\n{desc}"\
                    .format(signature=self.getSignature(),
                                  desc=lDesc)
    
    def getSignature(self):
        lRes = []
        for i in range(self._argCount):
            lCur = ""
            lArg = self._argSpec.args[1 + i]
            lAnno = self._argSpec.annotations.get(lArg, None)
            if i >= self._necessaryCount:
                lCur += "["
            lCur += "<{}".format(lArg)
            if lAnno is not None:
                assert isinstance(lAnno, ArgInterpreter)
                lCur += " : {}".format(lAnno.typeName)
            lCur += ">"
            lRes.append(lCur)
        if self._hasVarArgs:
            lArg = self._argSpec.varargs
            lAnno = self._argSpec.annotations.get(lArg, None)
            lCur = "[ ... ]"
            if lAnno is not None:
                assert isinstance(lAnno, ArgInterpreter)
                lCur = "[ ... : {}]".format(lAnno.typeName)
            lRes.append(lCur)
        return " ".join(lRes) + "]" * (self._argCount - self._necessaryCount)
    
    def getAnnoDescs(self):
        lRes = []
        lUsed = set()
        for lArg in self._argSpec.annotations:
            lAnno = self._argSpec.annotations[lArg]
            if lAnno.typeName in lUsed:
                continue
            lRes.append("`{name}` - {desc}".format(name=lAnno.typeName, desc=lAnno.desc))
            lUsed.add(lAnno.typeName)
        return "\n".join(lRes)
    
    def help(self, name=None):
        if name is None:
            name = self.function.__name__[3:]
        return self._help.format(name)
    
    def complete(self, argLine, text, begidx, endidx):  # TODO
        return []
#        lCheck, lArgs = self.parse(argLine)
#        if lCheck > 0:
#            return []
#        if lCheck == 0 and self._hasVarArg:
#            lAnno = self._argSpec.annotations.get(self._argSpec.varargs, None)
#            if lAnno is None:
#                return []
#            lCom = lAnno.complete(lArgs[-1])
#            # ? Maybe escape spaces, but for now - no
#            return lCom
#        lArgId = 1 + len(lArgs)
#        lAnno = self._argSpec.annotations.get(self._argSpec.args[lArgId], None)
#        if lAnno is None:
#            return []
#        lCom = lAnno.complete(lArgs[-1])
#        return lCom
    
    def parse(self, argLine):
        lParser = cmdargparse.CmdArgParser(argLine)
        lArgs = lParser.getArguments()
        if not self._hasVarArgs:
            lCheck = 0
            if len(lArgs) < self._necessaryCount:
                lCheck = -1
            if len(lArgs) > self._argCount:
                lCheck = 1
        else:
            lCheck = 0 if len(lArgs) >= self._necessaryCount else -1
        for i in range(min(len(lArgs), self._argCount)):
            lArgName = self._argSpec.args[i + 1]
            if lArgName in self._argSpec.annotations:
                lArgAnno = self._argSpec.annotations[lArgName]
                lArgs[i] = lArgAnno(lArgs[i])
        if self._hasVarArgs and lCheck == 0:
            lArgName = self._argSpec.varargs
            if lArgName in self._argSpec.annotations:
                lArgAnno = self._argSpec.annotations[lArgName]
                for i in range(self._argCount, len(lArgs)):
                    lArgs[i] = lArgAnno(lArgs[i])
        return lCheck, lArgs
    
    def __call__(self, wrappedSelf, argLine):
        try:
            check, cmdArgs = self.parse(argLine)
        except ValueError as e:
            wrappedSelf.log("Bad argument value: {0}".format(e), flair="error")
            return
        except cmdargparse.BaseException as e:
            wrappedSelf.log("Bad argument format: {0.text}".format(e), flair="error")
            return
        if check < 0:
            wrappedSelf.log("Not enough arguments", flair="error")
            return
        if check > 0:
            wrappedSelf.log("Too many arguments", flair="error")
            return
        return super().__call__(wrappedSelf, *cmdArgs)


class ArgInterpreter(general.StaticDecorator):
    def initParametric(self, typeName=None, desc="", strict=True, completer=lambda arg: []):
        if typeName is None:
            typeName = self.function.__name__
        self.typeName = typeName
        self.strict = strict
        self.desc = desc
        self.completer = completer
    
    def fail(self, arg):
        raise ValueError("Can't convert {value} to {type}".format(value=repr(arg), type=self.typeName))
    
    def __call__(self, arg):
        lRes = super().__call__(arg)
        if lRes is None and self.strict:
            self.fail(arg)
        return lRes
    
    def __getattribute__(self, attr):
        if attr in {"desc"}:
            val = super().__getattribute__(attr)
            if callable(val):
                return val()
            return val
        return super().__getattribute__(attr)


class ArgInterpreters:
    @ArgInterpreter.parametric(desc="True or false")
    def bool(arg):
        arg = arg.lower()
        if arg in ("false", "f", "0", "-", "no", "n", "off"):
            return False
        if arg in ("true", "t", "1", "+", "yes", "y", "on"):
            return True
        return None
    
    @ArgInterpreter.parametric(desc="An integer")
    def int(arg):
        try:
            return int(arg)
        except ValueError:
            return None


class Flair:
    format = "[{}]"
    
    def __init__(self, text, color):
        self.text = text
        self.color = color
        self.csiProvider = general.ColorProvider.getInstance()
    
    def getText(self):
        text = self.format.format(self.text)
        return self.csiProvider.wrap(text, self.csiProvider.fg + self.color)
    
    def __str__(self):
        return self.getText()


class Console(cmd.Cmd):
    name = "cmd"
    nohelp = "No help on {}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = ""
        self.prompting = False
        self.aliases = {}
        self.commands = set()
        self.legitCommands = set()
        self.csiProvider = general.ColorProvider.getInstance()
        self.namePalette = [self.csiProvider.underline]
        self.statePalette = [self.csiProvider.fg + self.csiProvider.red]
        self.flairSet = {"normal": Flair("*", self.csiProvider.cyan),
                          "warning": Flair("!", self.csiProvider.yellow),
                          "error": Flair("!", self.csiProvider.red)}
        self.flairEachLine = True
        for item in self.get_names():
            if item.startswith("do_"):
                self.commands.add(item[3:])
                self.legitCommands.add(item[3:])
        self.alias("quit", "exit")

    def __getattribute__(self, attr):
        if attr in {"prompt", "intro", "help", "state"}:
            val = super().__getattribute__(attr)
            if callable(val):
                return val()
            return val
        if attr.startswith("do_") and attr not in dir(self) and attr[3:] in self.aliases:
            return getattr(self, "do_" + self.aliases[attr[3:]])
        if attr.startswith("complete_") and attr not in dir(self) and attr[9:] in self.aliases:
            return getattr(self, "complete_" + self.aliases[attr[9:]])
        #if attr.startswith("complete_"):
        #    return getattr(self, "do_" + attr[9:]).complete
        return super().__getattribute__(attr)
    
    def precmd(self, line):
        self.prompting = False
        return super().precmd(line)
    
    def postcmd(self, stop, line):
        self.prompting = True
        return super().postcmd(stop, line)
    
    def prompt(self):
        lStateMark = ""
        lState = self.state
        if lState:
            if isinstance(lState, str):
                lStateMark = " ({state})".format(state=self.csiProvider.wrap(lState, *self.statePalette))
            elif isinstance(lState, (tuple, list)) and len(lState) == 2:
                lStateMark = " {category}({state})".format(category=lState[0], state=self.csiProvider.wrap(lState[1], *self.statePalette))
        return "{name}{stateMark} > ".format(name=self.csiProvider.wrap(self.name, *self.namePalette), stateMark=lStateMark)
    
    def emptyline(self):
        pass
    
    def log(self, *data, flair="normal"):
        if flair in self.flairSet:
            flair = self.flairSet[flair]
            if self.flairEachLine:
                data = " ".join(map(str, data)).split("\n")
                print(flair, end=" ")
                print(*data, sep="\n{} ".format(str(flair)))
            else:
                print(flair, *data)
        else:
            print(*data)
    
    def alias(self, source, *dest):
       for _dest in dest:
           self.commands.add(_dest)
           self.aliases[_dest] = source
    
    def onecmd(self, line):
        try:
            super().onecmd(line)
        except Exception as e:
            traceback.print_exc()  # Temporary
    
    def help(self):
        cmds = []
        inverseAliases = {}
        for dest in self.aliases:
            source = self.aliases[dest]
            inverseAliases[source] = inverseAliases.get(source, [])
            inverseAliases[source].append(dest)
        for cmd in sorted(self.legitCommands):
            if cmd in inverseAliases:
                cmds.append("{cmd} ({aliases})".format(cmd=cmd, aliases=", ".join(sorted(inverseAliases[cmd]))))
            else:
                cmds.append(cmd)
        header = ansi.brace("Avaivable commands", " ===[ ")
        header += "\n" + ansi.brace("Type \"help <command>\" for more info", " ===[ ")
        return "{header}\n{cmds}".format(header=header, cmds="\n".join(cmds))
    
    @staticmethod
    def completeList(text, array):
        return list(filter(lambda x: x.startswith(text), array))

    def completenames(self, text, *args):
        return self.completeList(text, self.commands)
    
    @Command.parametric("Exit the console")
    def do_quit(self):
        general.exit()
    
    @Command.parametric("Show help on the specified command")
    def do_help(self, command=None):
        if command is not None:
            if command in self.legitCommands:
                self.log(getattr(self, "do_{}".format(command)).help(command))
            elif command in self.aliases:
                self.log(getattr(self, "do_{}".format(self.aliases[command])).help("{}(={})".format(command, self.aliases[command])))
            else:
                self.log(self.nohelp.format(command))  # Temporary
        else:
            #return super(Console, self).do_help("")  # Temporary
            self.log(self.help)
    
    @Command.parametric("Set if colors and styles are applied to the output")
    def do_color(self, state: ArgInterpreters.bool):
        self.csiProvider.colorblind = not state
