# Flatcam TCL script to generate the g-code from Gerber file 


set_sys units MM
new

set page_width 210
set page_height 297

set root_path [open_folder]
set proj_name [file tail $root_path]
puts "Open CAM folder $root_path"

set top_gbr             [file join $root_path $proj_name-F_Cu.gtl]
set top_mask_gbr        [file join $root_path $proj_name-F_Mask.gts]

set bottom_gbr          [file join $root_path $proj_name-B_Cu.gbl]
set bottom_mask_gbr     [file join $root_path $proj_name-B_Mask.gbs]

set profile_gbr [file join $root_path $proj_name-Edge_Cuts.gm1]
set drill_xln   [file join $root_path $proj_name-PTH.drl]

puts "Top: $top_gbr"
puts "Bottom: $bottom_gbr"
puts "Profile: $profile_gbr"
puts "Drill: $drill_xln"


open_gerber "$top_gbr"      -outname  copper_top
open_gerber  "$top_mask_gbr" -outname mask_top
open_gerber  "$bottom_gbr"  -outname  copper_bottom
open_gerber  "$bottom_mask_gbr" -outname mask_bottom

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
aligndrill copper_bottom -axis Y -dist 0 -dia 3.17 -holes ($hole_x,0) -outname align_mark
drillcncjob align_mark -drillz -6 -travelz 4 -startz 4 -endxy 0,0 -endz 25 -feedrate_z 50 -feedrate_rapid 150 \
                     -spindlespeed 6000 -pp GRBL_11_no_M6 -outname align_mark_cnc

write_gcode align_mark_cnc [file join $root_path align_mark.nc]

plot_all

#Create bottom isolation 
isolate copper_bottom -dia 0.18 -passes 1 -overlap 30 -combine 1 -outname copper_bottom_iso
cncjob copper_bottom_iso -dia 0.18 -z_cut -0.06 -z_move 2 -feedrate 150 -feedrate_z 100  -feedrate_rapid 200 \
             -endz 25 -spindlespeed 10000 -dwelltime 1 -pp GRBL_11_no_M6 -outname copper_bottom_cnc
write_gcode copper_bottom_cnc [file join $root_path copper_bottom.nc]

#paint mask_bottom -tooldia 1.2 -offset 0.1 -method 'combo' -connect 1 -all -outname mask_bottom_clr
#cncjob mask_bottom_clr -dia 1.2 -z_cut -0.000001 -z_move 2 -feedrate 200 -feedrate_z 100  -feedrate_rapid 200 \
#             -endz 25 -spindlespeed 5000 -dwelltime 1 -pp duet3d -outname mask_bottom_cnc
#write_gcode mask_bottom_cnc [file join $root_path mask_bottom.nc] 



#Create Top isolation 
isolate copper_top -dia 0.18 -passes 1 -overlap 30 -combine 1 -outname copper_top_iso
cncjob copper_top_iso -dia 0.18 -z_cut -0.06 -z_move 2 -feedrate 150 -feedrate_z 100  -feedrate_rapid 200 \
             -endz 25 -spindlespeed 10000 -dwelltime 1 -pp GRBL_11_no_M6 -outname copper_top_cnc
write_gcode copper_top_cnc [file join $root_path copper_top.nc]

#paint mask_top -tooldia 1.2 -offset 0.1 -method 'combo' -connect 1 -all -outname mask_top_clr
#cncjob mask_top_clr -dia 1.2 -z_cut -0.000001 -z_move 2 -feedrate 200 -feedrate_z 100  -feedrate_rapid 200 \
#             -endz 25 -spindlespeed 5000 -dwelltime 1 -pp duet3d -outname mask_top_cnc
#write_gcode mask_top_cnc [file join $root_path mask_top.nc] -preamble "M3 10000" -postamble "M5"

#Create drill 
drillcncjob drill -drillz -2.5 -travelz 3 -startz 3 -endxy 0,0 -endz 30 -feedrate_z 100 -feedrate_rapid 150 \
                     -spindlespeed 10000 -endz 25 -pp GRBL_11_no_M6 -outname drill_cnc


write_gcode drill_cnc [file join $root_path drill.nc]


#Creat cutout 
geocutout profile -dia 2 -margin 0.1 -gapsize 0.5 -gaps tb -outname profile_ext

#if {[catch {isolate cutout -dia 2 -iso_type 1 -passes 1 -overlap 10 -combine 1  -outname profile_int} errmsg]} {
#    #join_geometry profile_cutout profile_ext  profile_ext
#} else {
#    #isolate cutout -dia 2 -iso_type 1 -passes 1 -overlap 10 -combine 1  -outname profile_int
#    #join_geometry profile_cutout profile_ext profile_int 
#    cncjob profile_int -dia 2 -z_cut -1.65 -dpp 0.9 -z_move 4 -feedrate 40 -feedrate_z 40  -feedrate_rapid 150 \
#         -endz 25 -spindlespeed 6000 -dwelltime 1 -pp GRBL_11_no_M6 -outname profile_cutout
#    write_gcode profile_cutout [file join $root_path profile_cutout.nc] 
#} 
cncjob profile_ext -dia 2 -z_cut -1.65 -dpp 0.9 -z_move 4 -feedrate 40 -feedrate_z 40  -feedrate_rapid 150 \
         -endz 25 -spindlespeed 6000 -dwelltime 1 -pp GRBL_11_no_M6 -outname profile_cnc
write_gcode profile_cnc [file join $root_path profile.nc] 

plot_all



