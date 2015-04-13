var movieEdition = function(movieProvider){
	var $dialog, $dialogTitle, $movieTitle, $movieId, $langOp, $languages, $audioVariants;
	var dialogSettings, self=this;

	var setupDialog = function(enableAudioVariants){
		if (!$dialog){
			$dialog = $('#dialog_movie_edition_lang');
			$dialogTitle = $('#dialog_title', $dialog);
			$movieTitle = $('#movie_title', $dialog);
			$languages = $('input[type="checkbox"]', $dialog);
			$langOp = $('input[name="lang.target"]', $dialog);
			$movieId = $('input[name="movie.id"]', $dialog);
			$audioVariants = $('.audio_variants', $dialog);
			dialogSettings = setupAjaxModal($dialog);
		}
		if (enableAudioVariants) $audioVariants.show();
		else $audioVariants.hide();
	}

	var editAudios = function($button, target, targetClass, enableAudioVariants){
		var movieInfo = movieProvider($button);
		var $ref = $button.parent();
		while ($ref.length && !$ref.hasClass('lang_dialog_wrapper')) $ref=$ref.parent();
		$ref=$ref.find(targetClass);
		if ($ref.length && movieInfo){
			setupDialog(enableAudioVariants);
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
	$('.audio-choice').off('click').click(function(){editAudios($(this), 'Audios', '.in-audios', true); return false;})
	$('.subtitle-choice').off('click').click(function(){editAudios($(this), 'Subtitles', '.in-subtitles', false);return false;})
};