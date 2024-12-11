
var urlCarrinhoPost = '';
var variacao_id = null;
var quantidade = 0;

$(document).ready(function(){

    $.ajaxSetup({
        headers:
        { 'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content') }
    });

    $("#closeDialogModal").click(function(){
        $("#dialogModal").hide();
    });

    $(".icone_remover_carrinho").click(function(){
        urlCarrinhoPost = $(this).data('url');
        variacao_id = $(this).data("variacao");
        $("#dialogModal").show();
    });
    
    //se deseja continuar com a exclusão do item
    $("#deleteItemCarrinho").click(function(){
        
        $("#dialogModal").hide();
        window.location.href = urlCarrinhoPost;

        $.ajax({
            type: "POST",
            dataType: "json",
            url: urlCarrinhoPost,
            data: {
                "variacaoid" : variacao_id,
                "csrfmiddlewaretoken": $('meta[name="csrf-token"]').attr('content')
            },
            success: function(jsonData) {   
                window.location.reload();        
            }
        });
    });
    
});

