include <variables_artificial_flower.scad>;

// Tube Holder
difference(){
translate([0, 0, h_base/2])
cube([l_base_thread,w_base,h_base], center=true);
//tube-top
translate([0 , 0, h_base/2 + 1])
cylinder(r=r_tube_top, h=h_tube_top);
////tube-bottom
translate([0, 0, -1])
cylinder(r=r_tube, h=h_base+2);

    //---same as flower-base---//
//Screw +x
translate([l_base_thread/2 - d_thread/2 - offset_thread , 0, -1])
cylinder(r=d_thread/2, h=h_base+2);
//Screw -x
translate([-(l_base_thread/2 - d_thread/2 - offset_thread), 0, -1])
cylinder(r=d_thread/2., h=h_base+2);
}