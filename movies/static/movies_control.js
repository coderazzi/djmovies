// var SubtitleDialog = function(){

// 	// this.onshown = function(){
// 	// 	this.$select
// 	// }

// 	this.show=function(){this.$dialog.modal('show');};
// 	var self=this;
// 	this.$dialog = $('#subtitle_dialog');
// 	this.$file = this.$dialog.find(':file')
// }

function setupMoviesControl() {
	var subtitleDialog;
	$('.ic_tooltip').tooltip();
	$('.ic_tooltip_img').tooltip({html: true, placement:'right', title:function(){
		return '<img src="'+$(this).attr('src')+'">';
	}});
	// $('.add_subtitles').click(function(){
	// 	if (!subtitleDialog) subtitleDialog = new SubtitleDialog();
	// 	subtitleDialog.show();
	// 	return false;
	// });
}