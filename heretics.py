import functools
import operator
import sopel

@sopel.module.rule(r'\b([a-zA-Z][a-zA-Z0-9\[\]\-\\`^{}\_]*) is a(?:n)? (heretic|haeretic|haeretick|heretick|heretike)\b')
@sopel.module.rule(r'\b([a-zA-Z][a-zA-Z0-9\[\]\-\\`^{}\_]*) are (heretic|haeretic|haeretick|heretick|heretike)s\b')
def denounce_heretic(bot, trigger):
    target = trigger.group(1)
    nick = trigger.nick
    channel = trigger.sender

    # Initialize the heretic
    denounce_key = 'denounce_%s' % str(target)
    defense_key = 'defense_%s' % str(target)
    denounce_history = bot.db.get_channel_value(channel, denounce_key)
    defense_history = bot.db.get_channel_value(channel, defense_key)
    if denounce_history is None or defense_history is None:
        denounce_history = []
        defense_history = []

    # Now actually do the work.
    if nick in defense_history:
        defense_history.remove(nick)

    if nick not in denounce_history:
        denounce_history.append(nick)

    set_heretic_values(bot, target, channel, denounce_history, defense_history)
    bot.say('noted')

@sopel.module.rule(r'\b([a-zA-Z][a-zA-Z0-9\[\]\-\\`^{}\_]*) is not a(?:n)? (heretic|haeretic|haeretick|heretick|heretike)\b')
@sopel.module.rule(r'\b([a-zA-Z][a-zA-Z0-9\[\]\-\\`^{}\_]*) are not (heretic|haeretic|haeretick|heretick|heretike)s\b')
def deny_heresy(bot, trigger):
    target = trigger.group(1)
    nick = trigger.nick
    channel = trigger.sender

    # Initialize the heretic
    denounce_key = 'denounce_%s' % str(target)
    defense_key = 'defense_%s' % str(target)
    denounce_history = bot.db.get_channel_value(channel, denounce_key)
    defense_history = bot.db.get_channel_value(channel, defense_key)
    if denounce_history is None or defense_history is None:
        denounce_history = []
        defense_history = []

    # Now actually do the work.
    if nick in denounce_history:
        denounce_history.remove(nick)

    if nick not in defense_history:
        defense_history.append(nick)

    set_heretic_values(bot, target, channel, denounce_history, defense_history)
    bot.say('noted')

def set_heretic_values(bot, target, channel, denunciations, defenses):
    denounce_key = 'denounce_%s' % str(target)
    defense_key = 'defense_%s' % str(target)
    bot.db.set_channel_value(channel, denounce_key, denunciations)
    bot.db.set_channel_value(channel, defense_key, defenses)

    all_heretics = bot.db.get_channel_value(channel, 'heretics')
    if all_heretics is None:
        all_heretics = [target]
    elif target not in all_heretics:
        all_heretics.append(target)
    bot.db.set_channel_value(channel, 'heretics', all_heretics)

def score(target, bot, channel):
    denounce_key = 'denounce_%s' % str(target)
    denounce_history = bot.db.get_channel_value(channel, denounce_key)
    heretic_count = 0
    if denounce_history is not None:
        heretic_count = len(denounce_history)

    defense_key = 'defense_%s' % str(target)
    defense_history = bot.db.get_channel_value(channel, defense_key)
    defense_count = 0
    if defense_history is not None:
        defense_count = len(defense_history)

    return (target, heretic_count - defense_count)

@sopel.module.commands('heretics')
@sopel.module.example('.heretics')
def heretics(bot, trigger):
    '''Lists the top X known heretics.'''
    num = 5
    channel = trigger.sender
    try:
        num = max(min(int(trigger.group(2)), 10), 1) # Restrict to 1 to 10 heretics to avoid spam (*ahem* ALETHEIST *ahem*)
    except:
        pass
    bot.say('Top %d Heretics' % num)
    all_heretics = bot.db.get_channel_value(channel, 'heretics')
    for i, heretic in enumerate([ x for x in sorted(map(functools.partial(score, bot=bot, channel=channel), all_heretics), key=operator.itemgetter(1), reverse=True) if x[1] > 0][:num]):
        bot.say('  #' + str(i + 1) + ' ' + heretic[0] + ' (' + str(heretic[1]) + ' denunciation' + ('s' if heretic[1] != 1 else '') + ')')

@sopel.module.commands('heretic')
@sopel.module.example('.heretic Spong')
def heretic(bot, trigger):
    '''Shows the "heretic score" of the given target, or the user if no target is given.'''
    target = trigger.nick
    channel = trigger.sender
    if trigger.group(2):
        target = trigger.group(2)

    total = score(target, bot, channel)[1]
    bot.say(target + ' (' + str(total) + ' denunciation' + ('s' if total != 1 else '') + ')')

@sopel.module.commands('denunciations', 'denounced', 'mh', 'myheretics', 'defenses', 'defended')
@sopel.module.example('.denounced')
@sopel.module.example('.defended WorfBot')
def denounced(bot, trigger):
    '''Either shows who the user has denounced/defended, or shows who has denounced/defended a target.'''
    channel = trigger.sender
    report = ''
    if trigger.group(2):
        target = trigger.group(2)
        denounced = bot.db.get_channel_value(channel, 'denounce_%s' % str(target)) or []
        defended = bot.db.get_channel_value(channel, 'defense_%s' % str(target)) or []

        if len(denounced) == 0:
            report = report + 'No one has denounced ' + target
        else:
            denouncers = ", ".join(denounced)
            report = report + target + ' has been denounced by: ' + denouncers

        if len(defended) == 0:
            report = report + ', and has not been defended by anyone.'
        else:
            defenders = ", ".join(defended)
            report = report + ', and has been defended by: ' + defenders

    else:
        all_heretics = bot.db.get_channel_value(channel, 'heretics')
        nick = trigger.nick
        denounced = [t for t in all_heretics if nick in bot.db.get_channel_value(channel, 'denounce_%s' % str(t))]
        defended = [t for t in all_heretics if nick in bot.db.get_channel_value(channel, 'defense_%s' % str(t))]
        
        if len(denounced) == 0:
            report = report + nick + ' has not denounced anything'
        else:
            string = ", ".join(denounced)
            report = report + nick + ' has denounced: ' + string

        if len(defended) == 0:
            report = report + ', and has not defended anything.'
        else:
            string = ", ".join(defended)
            report = report + ', and has defended: ' + string

    bot.say(report)
    
