# Flatcam TCL script to generate the g-code from KiCAD Gerber file 

puts "TCL Version: [info patchlevel]"

# Function to find a single file with a specific extension in a directory
# Parameters:
#   - dirPath: The directory to search in
#   - extension: The file extension to search for (with or without the leading dot)
# Returns: The full path of the found file
# Throws: An error if no file or multiple files are found
proc findSingleFileByExtension {dirPath extension} {
    # Normalize the extension (ensure it starts with a dot)
    if {[string index $extension 0] ne "."} {
        set extension ".$extension"
    }
    
    # Check if directory exists
    if {![file exists $dirPath] || ![file isdirectory $dirPath]} {
        error "Directory '$dirPath' does not exist or is not a directory"
    }
    
    # Search for files with the specified extension
    set matchPattern [file join $dirPath "*$extension"]
    set matchedFiles [glob -nocomplain $matchPattern]
    
    # Check if exactly one matching file exists
    set fileCount [llength $matchedFiles]
    
    if {$fileCount == 0} {
        error "No files with extension '$extension' found in $dirPath"
    } elseif {$fileCount > 1} {
        set fileList [join [lmap file $matchedFiles {file tail $file}] ", "]
        error "Multiple files with extension '$extension' found in $dirPath: $fileList"
    } else {
        # Only one file exists, return the full path
        return [lindex $matchedFiles 0]
    }
}

set_sys units MM
new

set root_path [open_folder]
set proj_name [file tail $root_path]
puts "Open CAM folder $root_path"

    set top_gbr             [findSingleFileByExtension $root_path gtl]
    set top_mask_gbr        [findSingleFileByExtension $root_path gts]
    set top_silk            [findSingleFileByExtension $root_path gto]

    set bottom_gbr          [findSingleFileByExtension $root_path gbl] 
    set bottom_mask_gbr     [findSingleFileByExtension $root_path gbs] 
    set bottom_silk         [findSingleFileByExtension $root_path gbo] 


    set profile_gbr [findSingleFileByExtension $root_path gm1] 
    set drill_xln   [findSingleFileByExtension $root_path drl] 




puts "Top: $top_gbr"
puts "Bottom: $bottom_gbr"
puts "Top Silk: $top_silk"
puts "Bottom Silk: $bottom_silk"

puts "Profile: $profile_gbr"
puts "Drill: $drill_xln"


open_gerber "$top_gbr"      -outname  copper_top
open_gerber  "$top_mask_gbr" -outname mask_top
open_gerber  "$top_silk" -outname silk_top


open_gerber  "$bottom_gbr"  -outname  copper_bottom
open_gerber  "$bottom_mask_gbr" -outname mask_bottom
open_gerber  "$bottom_silk" -outname silk_bottom

open_gerber  "$profile_gbr" -outname profile
open_excellon "$drill_xln"  -outname drill

set bbox [bounds profile]
set board_width [expr [lindex $bbox {0 2}]-[lindex $bbox {0 0}]]
set board_height [expr [lindex $bbox {0 3}]-[lindex $bbox {0 1}]]
set origin_x [expr ([lindex $bbox {0 0}]+[lindex $bbox {0 2}])/2]
set origin_y [expr ([lindex $bbox {0 1}]+[lindex $bbox {0 3}])/2]

puts "Move Origin by ($origin_x,$origin_y)"
set_origin -$origin_x,-$origin_y

#join_geometry mask_top_1 mask_top profile 
#join_geometry mask_bottom_1 mask_bottom profile 

#mirror mask_bottom_1 -axis Y -origin 0,0
#mirror mask_top_1 -axis Y -origin 0,0

#offset mask_bottom_1 [expr $page_width/4] [expr $page_height/4]
#offset mask_top_1 [expr $page_width/4+$page_width/2] [expr $page_height/4]
#join_geometry mask_page  mask_top_1 mask_bottom_1
#export_pdf mask_page [file join $root_path solder_mask.pdf] -bbox mask_page

#delete mask_page -f
#delete mask_top_1 -f
#delete mask_bottom_1 -f
#delete mask_top -f
#delete mask_bottom -f

mirror copper_bottom -axis X -origin 0,0
mirror mask_bottom -axis X -origin 0,0
mirror silk_bottom -axis X -origin 0,0

#offset mask_bottom [expr $board_width/2] [expr $board_height/2]
#offset mask_top [expr $board_width/2] [expr $board_height/2]

# Create solder mask laser removal code
# paint mask_bottom -tooldia 0.1 -offset 0.1 -method combo -all -outname mask_bottom_laser
# cncjob mask_bottom_laser -dia 0.1 -feedrate 400 -feedrate_z 500  -feedrate_rapid 3000 \
#             -endz 25 -spindlespeed 255 -pp Marlin_laser -outname mask_bottom_job
# write_gcode mask_bottom_job [file join $root_path mask_bottom_laser.nc]       

# paint mask_top -tooldia 0.1 -offset 0.1 -method combo -all -outname mask_top_laser
# cncjob mask_top_laser -dia 0.1 -feedrate 400 -feedrate_z 500  -feedrate_rapid 3000 \
#             -endz 25 -spindlespeed 255 -pp Marlin_laser -outname mask_top_job
# write_gcode mask_top_job [file join $root_path mask_top_laser.nc]  


# Create alignment drill 
set hole_x [expr [lindex [bounds profile] {0 0}]-6]
set hole_x -45
aligndrill copper_bottom -axis Y -dist 0 -dia 4 -holes ($hole_x,0) -outname align_mark
drillcncjob align_mark -drillz -6 -dpp 1 -travelz 2 -startz 5 -endxy 0,0 -endz 25 -feedrate_z 200 -feedrate_rapid 1000 \
                     -spindlespeed 10000 -pp Carvera -outname align_mark_cnc

write_gcode align_mark_cnc [file join $root_path align_mark.nc]

plot_all

#Create bottom isolation 
isolate copper_bottom -dia 0.15 -passes 1 -overlap 30 -combine 1 -outname copper_bottom_iso
cncjob copper_bottom_iso -dia 0.15 -z_cut -0.07 -startz 5 -z_move 2 -feedrate 1000 -feedrate_z 200  -feedrate_rapid 1000 \
             -endz 25 -spindlespeed 12000 -dwelltime 1 -pp Carvera -outname copper_bottom_cnc
write_gcode copper_bottom_cnc [file join $root_path copper_bottom.nc]

#Cereate bottom Solder Mask 
paint mask_bottom -tooldia 0.3 -method 'standard' -overlap 80 -connect 1 -contour 1 -all -outname mask_bottom_clr
cncjob mask_bottom_clr -dia 0.3 -z_cut -0.5  -startz 5 -z_move 2 -feedrate 400 -feedrate_z 200  -feedrate_rapid 1000 \
             -endz 25 -spindlespeed 6000 -dwelltime 1 -pp Carvera -outname mask_bottom_cnc
write_gcode mask_bottom_cnc [file join $root_path mask_bottom.nc] 

#Cereate bottom Silkscreen // Spindlespeed is now the laser power ratio
paint silk_bottom -tooldia 0.1 -method 'combo' -overlap 80 -connect 1 -contour 1 -all -outname silk_bottom_clr
cncjob silk_bottom_clr -dia 0.1 -z_cut -0.2 -z_move 2 -feedrate 100 -feedrate_z 200 -feedrate_rapid 1000 \
             -endz 25 -spindlespeed 20 -pp CarveraLaser -outname silk_bottom_cnc
write_gcode silk_bottom_cnc [file join $root_path silk_bottom.nc] 


#Create Top isolation 
isolate copper_top -dia 0.15 -passes 1 -overlap 30 -combine 1 -outname copper_top_iso
cncjob copper_top_iso -dia 0.15 -z_cut -0.07 -startz 5 -z_move 2 -feedrate 1000 -feedrate_z 200  -feedrate_rapid 1000 \
         -endz 25 -spindlespeed 12000 -dwelltime 1 -pp Carvera -outname copper_top_cnc
write_gcode copper_top_cnc [file join $root_path copper_top.nc]

#Create Top Solder Mask
paint mask_top -tooldia 0.3  -method 'combo' -connect 1 -contour 1 -all -outname mask_top_clr
cncjob mask_top_clr -dia 0.3 -z_cut -0.2 -startz 5 -z_move 2 -feedrate 400 -feedrate_z 200  -feedrate_rapid 1000 \
             -endz 25 -spindlespeed 6000 -dwelltime 1 -pp Carvera -outname mask_top_cnc
write_gcode mask_top_cnc [file join $root_path mask_top.nc] 

#Cereate Top Silkscreen // Spindlespeed is now the laser power ratio
paint silk_top -tooldia 0.1 -method 'combo' -overlap 80 -connect 1 -contour 1 -all -outname silk_top_clr
cncjob silk_top_clr -dia 0.1 -z_cut -0.2 -z_move 2 -feedrate 100 -feedrate_z 200 -feedrate_rapid 1000 \
             -endz 25 -spindlespeed 20 -pp CarveraLaser -outname silk_top_cnc
write_gcode silk_top_cnc [file join $root_path silk_top.nc] 

#Create drill 
drillcncjob drill -drillz -2 -dpp 1 -travelz 3 -startz 3 -endxy 0,0 -endz 25 -feedrate_z 200 -feedrate_rapid 1000 \
                     -spindlespeed 10000 -endz 25 -pp Carvera -outname drill_cnc


write_gcode drill_cnc [file join $root_path drill.nc]


#Creat cutout 
geocutout profile -dia 2 -margin 0.1 -gapsize 0.5 -gaps tb -outname profile_ext

#if {[catch {isolate cutout -dia 2 -iso_type 1 -passes 1 -overlap 10 -combine 1  -outname profile_int} errmsg]} {
#    #join_geometry profile_cutout profile_ext  profile_ext
#} else {
#    #isolate cutout -dia 2 -iso_type 1 -passes 1 -overlap 10 -combine 1  -outname profile_int
#    #join_geometry profile_cutout profile_ext profile_int 
#    cncjob profile_int -dia 2 -z_cut -1.65 -dpp 0.9 -z_move 4 -feedrate 40 -feedrate_z 40  -feedrate_rapid 150 \
#         -endz 25 -spindlespeed 6000 -dwelltime 1 -pp Carvera -outname profile_cutout
#    write_gcode profile_cutout [file join $root_path profile_cutout.nc] 
#} 
cncjob profile_ext -dia 2 -z_cut -1.65 -dpp 0.3 -z_move 3 -feedrate 500 -feedrate_z 300  -feedrate_rapid 500 \
         -endz 25 -spindlespeed 12000 -dwelltime 1 -pp Carvera -outname profile_cnc
write_gcode profile_cnc [file join $root_path profile.nc] 

plot_all



