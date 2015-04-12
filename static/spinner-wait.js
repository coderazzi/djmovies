//Spinner is a singleton to shown a waiting sign
var Spinner = {
	$spinner: null,
	count: 0, 
	show : function(){
		if (!this.$spinner){
			this.$spinner=$('#spinner-screen');
		}
		if (this.count===0){
			this.count=1;
			this.$spinner.show();
		}
	},
	hide : function(){
		if (this.count>0){
			this.count-=1;
			if (!this.count) this.$spinner.hide();
		}
	}
};
