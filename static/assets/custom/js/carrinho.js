
var urlCarrinhoPost = '';
var variacao_id = null;
var quantidade = 0;

$(document).ready(function(){

    $.ajaxSetup({
        headers:
        { 'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content') }
    });

    $("#continuar_comprando").on('click', function(e){

        url = $(this).attr('url-destino');
        dialogChangeQuantity(url);
    });

    function isQuantidadeAlterada(){
        var quantidadeAlterada = false;
        $('tr[data-quant]').each(function() {
            var $row = $(this);
            var quantidadeOriginal = $row.data('quant');
            quantidade  = $row.find('.quantidade').val();            

            if (quantidade != quantidadeOriginal) {
                quantidadeAlterada = true;
                return false; //return false to stop jquey loop
            }
        });
        if(quantidadeAlterada == true)
            return true;
        else
            return false;
    }

    $("#closeDialogModal2").click(function(){
        $("#dialogModal2").hide(); 
    });

    $("#closeDialogModal").click(function(){
        $("#dialogModal").hide();
    });

    $("#goToStore").click(function(){
        $("#dialogModal2").hide();
    });

    $("#finaliza_compra").click(function(){
        url = $(this).data('url');
        dialogChangeQuantity(url);
    });

    $("#btnFecharDialog2").on('click', function(){
        $("#dialogModal2").hide();     
    });

    $("#btnFecharDialog").on('click', function(){
        $("#dialogModal").hide();     
    });

    $("#changeCartQuantity").click(function(){
        
        urlDestino = $(this).data('url');
        $("#dialogModal").hide(); 
        $.ajax({
            type: "POST",
            dataType: "json",
            url: urlCarrinhoPost,
            data: {
                "variacaoid" : variacao_id,
                "quantidade": quantidade,
                "csrfmiddlewaretoken": $('meta[name="csrf-token"]').attr('content')
            },
            success: function(jsonData) {   
                console.log(jsonData);             
                $('tr[data-quant]').each(function() {
                    var $row = $(this);
                    if(variacao_id  == $row.data('variacaoid'))
                        $row.data('quant', quantidade);
                });
                dialogChangeQuantity(urlDestino)
            }
        });
    });
    
    function dialogChangeQuantity(urlDestino){
        
        if(isQuantidadeAlterada()){
            $('tr[data-quant]').each(function() {
                var $row = $(this);
                var quantidadeOriginal = $row.data('quant');
                var nomeProduto = $row.children('td.nome_produto').children('a').html();
                quantidade             = $row.find('.quantidade').val();            
                variacao_id            = $row.data('variacaoid');
                urlCarrinhoPost        = $(this).data('url');                
    
                if (quantidade != quantidadeOriginal) {
                    
                    quantidadeAlterada = true;
                    $("#dialogModal").find('button').attr('data-url', urlDestino)
                    $("#dialogModal").children('div')
                                        .children('div')
                                        .children('div.modal-body')
                                        .html('Tem certeza que deseja alterar a quantidade? do produto ' + nomeProduto + ' de ' + quantidadeOriginal + ' para ' + quantidade)
                    $("#dialogModal").show();
                    return false;
                }
            });      
        }
        if(!isQuantidadeAlterada())
            window.location.href = urlDestino;
    }

});

