

source_folder = "/Volumes/tmp/picard_music_identified/Artists"
convert_folder = "/Volumes/tmp/music_transcode_cache"

destination_folder = "/Volumes/MUSIC/Artists"

# destination_folder = "/Volumes/performance/VMs/node/filesForItunesMusic/Artists"

# 


# recommended relative to artists folder
playlist_folder = "../Playlists"

to_convert = [".flac", ".flc", ".m4a", ".mp2"] #also convert aac
valid_extension = [".mp3"] # TODO check if car supports .mp2

# subject to change..
playlist_extension = ".m3u8"


import os
import errno
import shutil
import audiotools


invalid_extensions_found = set()

"""

Assumptions made:
- folder structure is the same on source/destination
- any folders that exist on the destination and not on source are removed
- rest is synchronised
- all conversion is into .mp3

TODO
- add "dry run" to just display what would be done instead
    of doing any real modifications to the FS

"""
from os.path import join, getsize


# cleanup converted files if anything was removed in the source folder
for root, dirs, files in os.walk(convert_folder):        
    # does the path exist?
    current_path = os.path.relpath(root, start=convert_folder)
    source_corresponds = os.path.join(source_folder, current_path)
    
    print "Processing:", current_path, source_corresponds
    
    if not os.path.exists(source_corresponds):        
        print "Removing: ", root        
        shutil.rmtree(root)
    else:
        # now, check the files
        files_source = []
        for (dirpath, dirnames, fnames) in os.walk(source_corresponds):
            files_source.extend(fnames)
            break
        
        # change suffix to .mp3
        files_source = map(
            lambda fname: os.path.splitext(fname)[0]+".mp3", 
            files_source)
        
        extra_files = list(set(files) - set(files_source))
        # print extra_files
        for extra_file in extra_files:                           
            print "Found extra file, removing..", extra_file
            os.remove(os.path.join(root, extra_file))



# cleanup of the destination to remove anything not found in source
for root, dirs, files in os.walk(destination_folder):        
    # does the path exist?
    current_path = os.path.relpath(root, start=destination_folder)
    source_corresponds = os.path.join(source_folder, current_path)
    convert_corresponds = os.path.join(convert_folder, current_path)
    
    
    print "Processing:", current_path, source_corresponds
    
    if not os.path.exists(source_corresponds):        
        print "Removing: ", root        
        shutil.rmtree(root)
    else:
        # now, check the files
        files_source = []
        for (dirpath, dirnames, fnames) in os.walk(source_corresponds):
            files_source.extend(fnames)
            files_source = filter(lambda x: not x.startswith("._"), files_source)            
            break
        
        extra_files = list(set(files) - set(files_source))
        # print extra_files
        for extra_file in extra_files:            
            # could it possibly be a converted file?
            if os.path.exists(os.path.join(convert_corresponds, extra_file)):
                print "Found converted"
            else:                        
                print "Found extra file, removing..", extra_file
                os.remove(
                    os.path.join(destination_folder, current_path, extra_file))
                # print os.path.join(convert_corresponds, extra_file)
        

# investigate full set what needs to be copied
files_to_copy = []
files_to_convert = []
for root, dirs, files in os.walk(source_folder):
    
    # remove mac NFS metadata
    files = filter(lambda x: not x.startswith("._"), files)            
    
    
    def process_file(file):
        full_path = os.path.join(root, file)
        extension = os.path.splitext(full_path)[1]
        relative_path = os.path.relpath(full_path, start=source_folder)
        # print extension
        
        if extension in to_convert:            
            print "convert:", relative_path, extension
            files_to_convert.append((
                full_path, 
                os.path.join(destination_folder, relative_path)))
            
        elif extension not in valid_extension:
            invalid_extensions_found.add(extension)
            print "invalid ext:" , relative_path, extension
        else:
            # valid extension, copyting over                
            destination_file = os.path.join(
                destination_folder, relative_path)
            
            # add to to_copy list
            files_to_copy.append((full_path, destination_file))    
                
    map(process_file, files)



def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise


# convert 

failed_files = []
# convert files
def convert_file((source,destination), verbose=True): 
    try:   
        dest_format = ".mp3"

        destination_orig_suffix = os.path.splitext(destination)[1]
        relative_path = os.path.relpath(source, start=source_folder)
    
        convert_filename = os.path.join(
            convert_folder,     
            os.path.splitext(relative_path)[0]+dest_format)
    
        destination_filename = os.path.splitext(destination)[0]+dest_format

        # make dirs
        convert_dir = os.path.split(convert_filename)[0]
    
        def print_progress(x, y):
            print "%d%%" % (x * 100 / y)
    
        if not os.path.isfile(convert_filename):
            print "Converting: ", source        
            # make dir just in case
            mkdir_p(convert_dir) 
            infile = audiotools.open(source)
            # infile.verify()   
            # TODO change 
            conv_file = infile.convert(
                convert_filename, 
                audiotools.MP3Audio)
        
            conv_file.set_metadata(infile.get_metadata())
            # TODO detect keyboardErrors and remove file
            # in case it's incomplete
    
        # now copy the file over..
        if not os.path.isfile(destination_filename):
            dest_dir = os.path.split(destination_filename)[0]    
            # make dir just in case
            mkdir_p(dest_dir)
            # copy file
            shutil.copy2(convert_filename, dest_dir)
    
        return source,destination
    except Exception, e:
        print "Convert failed: ", source
        failed_files.append(source)
        
map(convert_file, files_to_convert)


# copy files without need of processing
def simple_copy((source, destination), verbose=True):
    dest_dir = os.path.split(destination)[0]
    
    # is it there already?
    if not os.path.isfile(destination):
        # make dir just in case
        mkdir_p(dest_dir)
        # copy file
        shutil.copy2(source, dest_dir)
        if verbose:
            print "copied: ", destination
    else:
        pass
        # just ignoring
        # TODO check file creation&modified date

    return source,destination

# TODO make nice progressbar
map(simple_copy, files_to_copy)


# process playlists
playlists_path = os.path.join(source_folder, playlist_folder)


playlist_relloc = os.path.relpath(playlists_path, start=source_folder)
playlist_dest = os.path.join(destination_folder, playlist_relloc)
shutil.rmtree(playlist_dest, ignore_errors=True)

for root, dirs, files in os.walk(playlists_path):        
    for file in [pls for pls in files if pls.endswith(playlist_extension) and not pls.startswith("._")]: 
        print "Processing playlist:", file
        
        with open(os.path.join(root, file), "r") as playlist_fp:
            playlist_content = playlist_fp.readlines()

        # replace all all file extensions
        to_replace = ["{}\r\n".format(suff) for suff in to_convert]
        replace_with = ".mp3\r\n"

        new_lines = []
        for line in playlist_content:
            cur_line = line
            for item in to_replace:
                if line.endswith(item):
                    cur_line = line[:-len(item)] + replace_with
                    break
            new_lines.append(cur_line)
            
        # store the playlist
        playlist_relloc = os.path.relpath(root, start=source_folder)
        playlist_dest = os.path.join(destination_folder, playlist_relloc)

        # create folder
        mkdir_p(playlist_dest)

        # write file
        pls_fname, ext = os.path.splitext(os.path.join(playlist_dest, file))        
        with open(pls_fname+".m3u", "w") as playlist_out:
            playlist_out.writelines(new_lines)

    

# cleanup
# remove all ._ files








