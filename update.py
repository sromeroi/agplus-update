#!Python:Python
#
# AMIGAGAMES+ UPDATER
# Simple script in ancient Python 1.4 to update AG+ based
# on a simple "code" file with "commands" and "arguments".
#
# The script is intended to run on an Amiga 1200 computer
# with Python 1.4 installed and under the AmigaGames+ disk.
# 
# Please note that this is python 1.4 (not real OOP, most of
# standard libraries present in nowadays python not available,
# True/False not existing, etc) so I had to take some licenses
# in the code...

import sys
import os
import glob
import shutil
import string
import regsub

# DH0: Workbench
# DH1: WHDload partition
# DH2: Applications partition
path_replacements = {
        "%WB%": "DH0:",
        "%WHDLOAD%": "DH1:",
        "%APPS%": "DH2:",
        "%OCS%": "DH1:",
        "%AGA%": "DH2:AGA",
        "%AGPLUS_HOME%": "S:",
        "%SPACE%": ' '
        }

replacements = {
        "\t": ' ',
        '//': '/',
        ':/': ':',
        '::': ':'
        }


#update_file="updates.csv"
update_file="updates.upd"

# Valid commands and number of arguments for each command
valid_cmd_and_args = { "COMMENT": 1,
                       "PRINT": 1,
                       "MKDIR": 1,
                       "RENAME": 2,
                       "DELETE": 1,
                       "DELETE_WITHOUT_ICON": 1,
                       "COPY": 2,
                       "COPY_WITHOUT_ICON": 2,
                       "MOVE": 2,
                       "MOVE_WITHOUT_ICON": 2,
                       "COPY_CONTENT": 2,
                       "CONFIRM_BEGIN": 3,
                       "CONFIRM_END": 0,
                       "CONFIRM_ELSE": 0,
                       "IF_EXISTS": 1,
                       "IF_NOT_EXISTS": 1,
                       "IF_EXISTS_END": 0,
                       "IF_EXISTS_ELSE": 0,
                       "EXECUTE": 1,
                       "END": 0,
                       "INCLUDE": 1,
                       "PASS": 0
                     }


#----------------------------------------------------------------------
def startsWith( item, substr ):
    """Returns 1 if string item starts with substr."""
    longSub = len(substr)
    if item[:longSub] == substr:
        return 1
    return 0


#----------------------------------------------------------------------
def endsWith( item, substr ):
    """Returns 1 if string item ends with substr."""
    longSub = -( len(substr) )
    if item[longSub:] == substr:
        return 1
    return 0


#----------------------------------------------------------------------
def rmTree(folder):
    """Custom shutils.rmTree equivalent"""

    if not os.path.exists(folder): return

    items_hidden = glob.glob( os.path.join(folder, '.*') )
    items = glob.glob( os.path.join(folder, '*') )
    items = items + items_hidden

    for item in items:
        if os.path.isdir(item):
            rmTree(item)
        else:
            os.remove(item)

    if os.path.exists(folder):
        os.remove(folder)


#----------------------------------------------------------------------
def do_variables_replacement(item):
    """Replace PATH variables in string."""
    for key in path_replacements.keys():
        item = regsub.gsub( key, path_replacements[key], item )
    for key in replacements.keys():
        item = regsub.gsub( key, replacements[key], item )
    item = string.strip(item)
    if endsWith(item, '/'): item = item[:-1]
    item = string.strip(item)
    return item


#----------------------------------------------------------------------
def critical_error(numline, command, text=''):
    """Critical error (print info and avoid execution)"""
    print "\nERROR: Error ejecutando " + command + " (linea " + str(numline) + ")."
    if len(text) > 0:
        print "\nERROR CODE: [" + text + "]"
    try: raw_input("\n-- Actualizacion abortada - pulsa ENTER para continuar --")
    except: pass
    sys.exit(1)


#----------------------------------------------------------------------
def unknown_action(action, numline, command):
    """Unknown action message."""
    print "\nWARNING: Comando desconocido " + command + " en linea " + str(numline) + "\n"
    sys.exit(1)


#----------------------------------------------------------------------
def mkdir_p(dirpath, numline, command):
    """Recursive mkdir function"""

    if os.path.exists(dirpath) and os.path.isdir(dirpath):
        return

    if os.path.exists(dirpath):
        critical_error(numline, command, 'El destino ya existe y no es un directorio')

    h,t = os.path.split(dirpath) # head/tail
    if not os.path.isdir(h):
        mkdir_p(h, numline, command)

    os.mkdir( os.path.join(h, t) )


#----------------------------------------------------------------------
def rename(source, dest, numline, command, ignore_errors=0):
    """Rename function"""
    if os.path.exists(dest) and not ignore_errors:
        critical_error(numline, command, 'Ya existe un destino con ese nombre')
    try:
        os.rename(source, dest)
    except:
        if not ignore_errors:
            critical_error(numline, command, '')


#----------------------------------------------------------------------
def delete(item, numline, command, ignore_errors=0):
    """Delete file or folder function"""

    # Destination does not exist: ok!
    if not os.path.exists(item):
        return

    try:
        # For folders use shutil.rmtree, for files os.remove:
        if os.path.isdir(item):
            rmTree(item)
        else:
            os.remove(item)
    except:
        if not ignore_errors:
            critical_error(numline, command, '')


#----------------------------------------------------------------------
def copy(source, dest, numline, command, ignore_errors=0):
    """Copy file/folder function"""

    # If source file does not exist -> error
    if not os.path.exists(source):
        if ignore_errors:
            return
        critical_error(numline, command, 'El origen especificado no existe')

    source_is_dir = os.path.isdir(source)
    dest_is_dir = os.path.isdir(dest)
    dest_exists = os.path.exists(dest)

    if dest_exists and dest_is_dir:
        name = os.path.basename(source)
        dest = os.path.join(dest, name)

    try:
        if source_is_dir:
            shutil.copytree(source, dest)
        else:
            shutil.copyfile(source, dest)
    except:
        if not ignore_errors:
            critical_error(numline, command, '')


#----------------------------------------------------------------------
def move(source, dest, numline, command, ignore_errors=0):
    """Move file/folder function"""

    copy( source, dest, numline, command, ignore_errors)
    delete( source, numline, command, ignore_errors)


#----------------------------------------------------------------------
def copy_content(source, dest, numline, command, ignore_errors=0):
    """Copy content of folder to dest folder"""

    if not os.path.exists(source) or not os.path.isdir(source):
        critical_error(numline, command, 'el origen especificado no existe o no es un directorio')

    if not os.path.exists(dest) or not os.path.isdir(dest):
        critical_error(numline, command, 'el destino especificado no existe o no es un directorio')
    files = glob.glob( os.path.join(source, "*") )
    for src in files:
        copy( src, dest, numline, command )


#----------------------------------------------------------------------
def parse_file( filename, code_format, skipping ):
    """Parse specified code file."""

    try:
        fp = open(filename, "r")
    except:
        print "\nERROR: No se pudo abrir el fichero " + file
        raw_input("\n-- Actualizacion abortada - pulsa ENTER para continuar --")
        sys.exit(1)

    code = []
    lines = []

    i = 0
    for line in fp.readlines():
        i = i +1
        line = do_variables_replacement(line)
        line_upper = string.upper( string.strip(line) )

        # Skip empty lines
        if len(line_upper) == 0 or startsWith(line_upper, "#"):
            continue

        num_line = "'%s:%d'" % (filename, i)
        tokens, skipping = parse_line(line, num_line, line, code_format, skipping)

        if len(tokens) > 0:
            action = tokens[0]

            if action == "INCLUDE":
                included_code, included_lines, skipping = parse_file(tokens[1], code_format, skipping)
                code = code + included_code
                lines = lines + included_lines

            code.append(tokens)
            lines.append(num_line)

    fp.close()

    return code, lines, skipping


#----------------------------------------------------------------------
def parse_line(line, numline, command, code_format, skipping ):
    """Parse line and generate tokens for later execution."""

    tokens = []
    skip_until_confirm_end = skipping[0]
    skip_until_if_exists_end = skipping[1]

    #-- 1.- Get ACTION --
    if code_format == 0:
        temp = string.split(line,";")

    elif code_format == 1:
        temp = string.split(line, ' "')

    action = string.strip(temp[0])

    #-- 2.- Check for not valid actions --
    if not action in valid_cmd_and_args.keys():
        unknown_action(action, numline, command)
        return [], [ skip_until_confirm_end, skip_until_if_exists_end ]

    #-- 3.- Extract parameters --
    if code_format == 0:
        if not ";" in line and action == "PRINT": line = line + ";"
        tokens = string.split(line, ";")

    elif code_format == 1:
        for item in temp:
            item = string.rstrip(item)
            if endsWith(item, '"'): item = item[:-1]
            item = string.rstrip(item)
            tokens.append(item)
        if action == "PRINT" and len(tokens) == 1:
            tokens.append('')

    # Force Action to be our cleaned action
    tokens[0] = action

    # get first char of the action:
    first_char = ''
    if len(action) > 0:
        first_char = action[0]

    # skip comments (and commands starting with '#')
    if first_char == '#' or action == "COMMENT" or action == "#" or action == '---':
        return [], [ skip_until_confirm_end, skip_until_if_exists_end ]

    #-- 4.- Check number of arguments --
    num_args = len(tokens) - 1
    required_args = valid_cmd_and_args[action]
    if required_args != num_args:
        critical_error(numline, command, 'Faltan argumentos para el comando')

    required_dquotes = required_args * 2
    num_dquotes = string.count(line, '"')

    if num_dquotes < required_dquotes:
        if not ( action == "PRINT" and num_dquotes == 0 ):
            critical_error(numline, command, 'Falta una o mas comillas dobles (") en el comando')
    elif num_dquotes > required_dquotes:
        critical_error(numline, command, 'Sobra una o mas comillas dobles (") en el comando')

    # Check CONFIRM_END
    if action == "CONFIRM_END":
        if skip_until_confirm_end == 1:
            skip_until_confirm_end = 0
        else:
            critical_error(numline, command, 'CONFIRM_END without CONFIRM_BEGIN')

    elif action == "CONFIRM_BEGIN":
        skip_until_confirm_end = 1

    # Check IF_EXISTS_END
    if action == "IF_EXISTS_END":
        if skip_until_if_exists_end == 1:
            skip_until_if_exists_end = 0
        else:
            critical_error(numline, command, 'IF_EXISTS_END without IF_EXISTS / IF_NOT_EXISTS')

    elif action == "IF_EXISTS" or action == "IF_NOT_EXISTS":
        skip_until_if_exists_end = 1

    #-- 5.- Return tokenized line --
    return tokens, [ skip_until_confirm_end, skip_until_if_exists_end ]


#----------------------------------------------------------------------
def run_command(tokens, numline, command, skipping):
    """run command. used for each line of the csv file"""

    action = tokens[0]

    try:               arg1 = tokens[1]
    except IndexError: arg1 = '';
    try:               arg2 = tokens[2]
    except IndexError: arg2 = '';
    try:               arg3 = tokens[3]
    except IndexError: arg3 = '';

    # Start executing commands
    skip_until_confirm_end = skipping[0]
    skip_until_if_exists_end = skipping[1]

    #-- (begin) CONFIRM_*
    if action == "CONFIRM_END":
        skip_until_confirm_end = 0
        return [skip_until_confirm_end, skip_until_if_exists_end]

    elif action == "CONFIRM_ELSE":
        skip_until_confirm_end = 1 - skip_until_confirm_end
        return [skip_until_confirm_end, skip_until_if_exists_end]

    # If we are in "CONFIRM" mode, skip every line until a CONFIRM_END is found
    if skip_until_confirm_end:
        return [skip_until_confirm_end, skip_until_if_exists_end]

    #-- (end) CONFIRM_*

    #-- (begin) IF_EXISTS_*
    elif action == "IF_EXISTS_END":
        skip_until_if_exists_end = 0
        return [skip_until_confirm_end, skip_until_if_exists_end]

    elif action == "IF_EXISTS_ELSE":
        skip_until_if_exists_end = 1 - skip_until_if_exists_end
        return [skip_until_confirm_end, skip_until_if_exists_end]

    if skip_until_if_exists_end:
        return [skip_until_confirm_end, skip_until_if_exists_end]
    #-- (end) IF_EXISTS_*

    if action == "PRINT":
        text = regsub.gsub( '%CR%', "\n", arg1 )
        print regsub.gsub( '%%', '"', text )

    elif action == "MKDIR":
        mkdir_p(arg1, numline, command)

    elif action == "RENAME":
        rename(arg1, arg2, numline, command)
        rename(arg1 + ".info", arg2 + ".info", numline, command, 1)

    elif action == "DELETE":
        delete(arg1, numline, command)
        delete(arg1 + ".info", numline, command, 1)

    elif action == "DELETE_WITHOUT_ICON":
        delete(arg1, numline, command)

    elif action == "COPY":
        copy(arg1, arg2, numline, command)
        copy(arg1 + ".info", arg2, numline, command, 1)

    elif action == "COPY_WITHOUT_ICON":
        copy(arg1, arg2, numline, command)

    elif action == "MOVE":
        move(arg1, arg2, numline, command)
        move(arg1 + ".info", arg2, numline, command, 1)

    elif action == "MOVE_WITHOUT_ICON":
        move(arg1, arg2, numline, command)

    elif action == "COPY_CONTENT":
        copy_content(arg1, arg2, numline, command)

    elif action == "EXECUTE":
        os.system(arg1)

    elif action == "PASS":
        pass

    elif action == "CONFIRM_BEGIN":
        done = 0
        while not done:
            confirm = raw_input(arg1 + " ")
            # arg2 = option that RUNs
            if confirm == arg2:
                skip_until_confirm_end = 0
                done = 1
            # arg3 = option that SKIPs
            elif confirm == arg3:
                skip_until_confirm_end = 1
                done = 1

    elif action == "IF_EXISTS":
        if os.path.exists(arg1):
            skip_until_if_exists_end = 0
        else:
            skip_until_if_exists_end = 1

    elif action == "IF_NOT_EXISTS":
        if os.path.exists(arg1):
            skip_until_if_exists_end = 1
        else:
            skip_until_if_exists_end = 0

    # Go back to loop return the status of skipping
    return [skip_until_confirm_end, skip_until_if_exists_end]


#----------------------------------------------------------------------
def main():
    """Main function"""

    # code_format is CSV (0) or UPD (1)
    code_format = 0
    if endsWith( string.upper(update_file), "UPD"): code_format = 1

    # [ skip_if_confirm, skip_if_exists ]
    skip = [0, 0]

    code, lines, _ = parse_file(update_file, code_format, skip)

    for i in range(0,len(code)):

        skipping = skip[0] == 1 or skip[1] == 1
        tokens = code[i]
        command = string.join(tokens, " ")
        numline = lines[i]
        action = tokens[0]

        # End of program?
        if action == "END":
            if skipping: continue
            else      :  break

        skip = run_command(tokens, numline, command, skip)

    try:    raw_input("\n-- Actualizacion finalizada - pulsa ENTER para continuar --")
    except: pass


#----------------------------------------------------------------------
if __name__ == "__main__":
    main()
