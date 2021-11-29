#!/usr/bin/env python3
import re
import traceback
import logging
log = logging.getLogger()


def refac_do(filename,args):
  if (not args.free_form) and (not args.fixed_form):
    #autodetermine form
    if filename[-3:] == "f90":
      free_form = True
    else:
      free_form = False
  else:
    free_form = args.free_form

  log.info("parsing as fortran free_form: " + repr(free_form))

  if free_form:
    # do label statement pattern
    do_label_re = re.compile('^([ 0-9]*)do[ ]{1,}([0-9]{1,})[ ]{1,}')
  else:
    do_label_re = re.compile('^([ 0-9]{5,})do[ ]{1,}([0-9]{1,})[ ]{1,}')

  # label statement pattern
  label_re = re.compile('^[ ]*([0-9]{1,})[ ]*')
  # goto statement pattern
  goto_re = re.compile('[ ]+go *to[ ]+([0-9]{1,})')
    
  dos = []
  gotos = []

  # stack of do's not closed
  do_stack = []
  # indent of said do's
  do_indent = []

  try:
    contents = open(filename,"r").readlines()
  except:
    log.error(traceback.format_exc())
    return

  for i in range(len(contents)):
    line = contents[i]
    # search for statements

    match = do_label_re.match(line)
    if match:
      # append to stack of dos found
      log.info("We have found do statement   : %s"%match.group(2))
      dos.append(match.group(2))
      do_stack.append(match.group(2))
      do_indent.append(len(match.group(1)))
      line = re.sub('do[ ]{1,}([0-9]{1,})',"do",line)
      contents[i] = line

    match = label_re.match(line)
    if match:
      # pop dos in reverse order, addend do per label match, remove continue
      log.info("We have found label statement: %s"%match.group(1))
      if len(do_stack) > 0:
        # do we have to edit?
        if do_stack[-1] == match.group(1):

          #Check for multiline, and add it accordingly
          j = i+1
          try:
            while contents[j][5] == '&' or contents[j-1][-2] == '&': 
              line = line + contents[j]
              contents[j] = "" #remove since we add it here
              j += 1
          except IndexError:
            pass
          
          #Remove continue and label except if there is an goto pointing to it
          if not match.group(1) in gotos:
            line_s = re.sub("^([ 0-9])*"," ",line)
            line = " "*(len(line)-len(line_s)) + line_s
            line = re.sub(" *continue.*\n","", line)
            #also remove  end[ ]do, we will add it later ....
            line = re.sub(" *end *do.*\n","", line)
          while do_stack[-1] == match.group(1):
            line += " "*do_indent[-1] + "enddo\n"
            do_stack.pop()
            do_indent.pop()
            if len(do_stack) == 0:
              break
          contents[i] = line

    match = goto_re.search(line)
    if match:
      log.info("We have found goto statement : %s"%match.group(1))
      gotos.append(match.group(1))

  log.debug(do_stack)

  # Sanity checks
  overlap = list(set(dos) & set(gotos)) 
  if len(overlap) > 0:
      log.warning("GOTO and DO label " + repr(overlap) + " overlap")

  if len(do_stack) > 0:
    log.error("unclosed DO label detected " + repr(do_stack) + ", exiting...")
    return
    
  # write back
  if args.e:
    with open(file,"w") as f:
      f.write("".join(contents))
  else:
    print("".join(contents),end="")
      
    
    
if __name__ == '__main__':
  """Parse the command line arguments."""
  import argparse
  parser = argparse.ArgumentParser(
      description="refactor some fortran files")
  parser.add_argument('files', metavar='file', nargs='+',
                    help='files to process')
  parser.add_argument( '-e', default=False, action='store_const'
                     , const = True
                     , help="edit files in place, default is stdout")
  group = parser.add_mutually_exclusive_group()
  group.add_argument( '-free-form', default=False, action='store_const'
                     , const = True
                     , help="file is F90 free form")
  group.add_argument( '-fixed-form', default=False, action='store_const'
                     , const = True
                     , help="file is F90 fixed form")
  parser.add_argument( '--logfile', metavar='FILE', default=False
                     , help="output performed work to logfile, default is stderr")
  parser.add_argument( '--loglevel', metavar='LEVEL', default=20, type=int
                     , help="logging level [0,10,20,30,40,50] lower is more")
  args = parser.parse_args()


  logging.basicConfig(level=args.loglevel)

  for file in args.files:
    log.info("processing %s"%file)
    refac_do(file, args)

 
