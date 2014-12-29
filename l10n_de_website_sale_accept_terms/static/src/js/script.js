jQuery("document").ready(function($) {
    
    //show and hide functions for the terms and revocation popup
    $("#close-terms").click(function() {
        $("#wsga-terms").hide("slow");
    });    
        
    $("#open-terms").click(function() {
        $("#wsga-terms").show("slow");
    });
    
    $("#close-revo").click(function() {
        $("#wsga-revo").hide("slow");
    });    
        
    $("#open-revo").click(function() {
        $("#wsga-revo").show("slow");
    });
	
});