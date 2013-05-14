var movieEdition = function(movieProvider){

	var $dialog, $dialogTitle, $movieTitle, $movieId, $langOp, $languages;
	var dialogSettings, self=this;

	var setupDialog = function(){
		if (!$dialog){
			$dialog = $('#movie_edition_lang_dialog');
			$dialogTitle = $('#dialog_title', $dialog);
			$movieTitle = $('#movie_title', $dialog);
			$languages = $('input[type="checkbox"]', $dialog);
			$langOp = $('input[name="lang.target"]', $dialog);
			$movieId = $('input[name="movie.id"]', $dialog);
			dialogSettings = setupAjaxModal($dialog);
		}
	}

	var editAudios = function($button, target, targetClass){
		var movieInfo = movieProvider($button);
		var $ref = $button.parent();
		while ($ref.length && !$ref.hasClass('lang_dialog_wrapper')) $ref=$ref.parent();
		$ref=$ref.find(targetClass);
		if ($ref.length && movieInfo){
			setupDialog();
			var value = $ref.text();
			var len = $languages.length;
			while (len-- > 0){
				var $l=$languages[len];
				$l.checked = value.indexOf($l.value)==-1? '' : 'checked';
			}
			$movieId.val(movieInfo[0]);
			$movieTitle.text(movieInfo[1]);
			$dialogTitle.text(target);
			$langOp.val(target);
			dialogSettings.message=target+' update';
			dialogSettings.settings.success=function(response){
				$ref.text(response);
				$dialog.modal('hide');
			};
			$dialog.modal('show');
		}
	}

	$('.ic_tooltip').tooltip();
	$('.ic_tooltip_img').tooltip({html: true, placement:'right', title:function(){
		return '<img src="'+$(this).attr('src')+'">';
	}});
	$('.audio-choice').click(function(){editAudios($(this), 'Audios', '.in-audios');})
	$('.subtitle-choice').click(function(){editAudios($(this), 'Subtitles', '.in-subtitles');})
};