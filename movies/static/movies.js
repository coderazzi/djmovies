var firstMovieDiv, moviesDiv;

function handleResize(event){
	var width = $(window).width();
	var oneWidth = firstMovieDiv.width();
	var padding = (width -Math.floor(width / oneWidth)*oneWidth)/2;
	moviesDiv.css('padding-left', padding+'px');
}

$(function() {
	moviesDiv = $('#div_movies');
	firstMovieDiv=$('.div_movie:first', moviesDiv)

	if (firstMovieDiv.length>0){
		handleResize();
		$(window).resize(handleResize);
	}

});
