include <variables_artificial_flower.scad>;

// Print Flower
rotate_extrude($fn = fn_corolla_pelets) // 360 degree rotate
{
    //corolla
    translate([l_flower+r_nectory, l_additional_corolla_pipe, 0])
    difference(){
        circle(r = l_flower, $fn = fn_petels_surface, center = true); // outer layer
        circle(r = (l_flower-thick_flower) , $fn = fn_petels_surface, center = true); // inner layer
        // remove 3/4 of the circle
        polygon( points=[[0,0], [0,l_flower], [l_flower,l_flower], 
        [l_flower,-l_flower], [-l_flower,-l_flower], [-l_flower, 0]]);
    }
    // petels
    translate([r_nectory+l_flower, l_additional_corolla_pipe+l_flower-thick_flower, 0])
    square([l_petel,thick_flower]);
    //additional-pipe-base
    translate([r_nectory, 0, 0])
    square([thick_flower,l_additional_corolla_pipe]);
}

// Flower-base
difference(){
translate([0, 0, h_base/2])
cube([l_base_thread,w_base,h_base], center=true);
translate([0, 0, -1])
cylinder(r=r_nectory+1, h=h_base+2);
//Screw +x
translate([l_base_thread/2 - d_thread/2 - offset_thread , 0, -1])
cylinder(r=d_thread/2, h=h_base+2);
//Screw -x
translate([-(l_base_thread/2 - d_thread/2 - offset_thread), 0, -1])
cylinder(r=d_thread/2., h=h_base+2);
}