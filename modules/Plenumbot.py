import sopel.module
from datetime import datetime,  timedelta
from urllib import request
from py_etherpad import EtherpadLiteClient
import re

etherpad = None
identifier = "---FREIFUNK DARMSTADT PLENUM---"

@sopel.module.commands('pad')
def padlink(bot, trigger):
    bot.say(bot.memory["etherpad"]+"/p/"+bot.memory["padid"])

@sopel.module.commands('tops')
def gettop(bot, trigger):
    bot.memory["tops"] = gettops(etherpad.getText("ffda-"+bot.memory["nextplenum"].strftime("%Y%m%d"))['text'])
    topics = bot.memory["tops"]
    it = 0
    for key in topics:
        it += 1
        bot.say(str(it)+". "+key[1]+" ["+key[0]+"]")

@sopel.module.commands('add')
def addtop(bot, trigger):
    if len(trigger.args) > 1:
        command = trigger.args[1].split()
        if len(command) < 2:
            bot.say("Falsche Argumente: Benutzung .add Inhaber Dauer Thema")
            return
        else:
            tops = bot.memory["tops"]
            newtop = [command[1], " ".join(command[3:])]
            tops.append(newtop)
        try: text = etherpad.getHtml(bot.memory["padid"])["html"]
        except:
            bot.say('Konnte Pad nicht aufrufen')
            return
        text = text.replace('</ol>&lt;&#x2F;tops&gt;', '<li>[' + command[1] + '] '+command[2] +"' "  + newtop[1] + '</li></ol>&lt;&#x2F;tops&gt;')
        try: etherpad.setHtml(bot.memory["padid"], text)
        except:
            pass
    else:
        bot.say("Falsche Argumente: Benutzung .add Inhaber Dauer Thema")

def setup(bot):
    global etherpad
    bot.memory["rythm"] = int(bot.config.plenum.rythm)
    date = [int(i) for i in bot.config.plenum.startdate.split(".")[::-1]]
    bot.memory["nextplenum"] = nextmeeting(datetime(*date), bot.memory["rythm"])
    bot.memory["etherpad"] = bot.config.plenum.etherpadurl
    bot.memory["apikey"] = bot.config.plenum.apikey
    bot.memory["padid"] = "ffda-"+bot.memory["nextplenum"].strftime("%Y%m%d")
    updatetemplate(bot, bot.config.plenum.template)
    etherpad = EtherpadLiteClient(bot.memory["apikey"], bot.memory["etherpad"]+"/api")
    padsetup(bot)

def updatetemplate(bot, template):
    try:
        temptemplate = request.urlopen(template).read().decode('utf-8')
    except:
        raise Exception("No template")
    templatefile = open("template", "w")
    templatefile.write(temptemplate)
    templatefile.close()
    bot.memory["template"] = temptemplate

def padsetup(bot):
    bot.memory["tops"] = []
    try:
        etherpad.createPad("ffda-"+bot.memory["nextplenum"].strftime("%Y%m%d"))
    except ValueError:
        text = etherpad.getText(bot.memory["padid"])["text"]
        if checkpad(text):
            bot.memory["tops"] = gettops(text)
            return
        else:
            if "Welcome to Etherpad!" in text:
                try: etherpad.setText("ffda-"+bot.memory["nextplenum"].strftime("%Y%m%d"), "")
                except:
                    print("General error")
            else:
                #bot.say('Jemand hat das Plenumspad zerstört')
                print("Problem mit dem Pad")
                return
    template = bot.memory["template"]
    template = template.replace('#DATE#', bot.memory["nextplenum"].isoformat())

    # TODO add last plenum recap
    # template = template.replace('#NEXTPLENUM#', ...)
    etherpad.setText("ffda-"+bot.memory["nextplenum"].strftime("%Y%m%d"), template)


def checkpad(padtext):
    if identifier in padtext.partition("\n")[0]:
        return True
    return False

def gettops(padtext):
    try:
        padtops = re.findall(r'(?<=\<tops\>)[\s\S]*(?=</tops>)', padtext)[0]
    except IndexError:
        return []
    tops = []
    for match in re.findall("\[.*\].*", padtops):
        try: tops.append([re.findall('\[.*\]', match)[0].strip("[]"), re.split('\]', match)[1]])
        except:
            pass
        print(tops)
    return tops

def nextmeeting(last, rythm):
    rythmdays = rythm * 7
    delt = datetime.now() - last
    if delt.days < rythmdays:
        return last + timedelta(14)
    else:
        diff = delt.days % rythm * 7
        if diff == 0:
            return last
        return datetime.now() + timedelta(rythmdays - diff)