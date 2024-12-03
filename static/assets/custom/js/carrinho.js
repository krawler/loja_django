
var urlCarrinhoPost = '';
var urlDestinoContinuar = '';
var variacao_id = null;
var quantidade = 0;
var quantidadeAlterada = false;
$(document).ready(function(){

    $.ajaxSetup({
        headers:
        { 'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content') }
    });

    $("#continuar_comprando").on('click', function(e){

        dialogChangeQuantity();
    });

    function isQuantidadeAlterada(){
        $('tr[data-quant]').each(function() {
            var $row = $(this);
            var quantidadeOriginal = $row.data('quant');
            quantidade  = $row.find('.quantidade').val();            

            if (quantidade != quantidadeOriginal) {
                quantidadeAlterada = true;
                return false;
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
        dialogChangeQuantity();
    });

    $("#btnFecharDialog2").on('click', function(){
        $("#dialogModal2").hide();     
    });

    $("#changeCartQuantity").click(function(){
        
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
                quantidadeAlterada = false;
                $('tr[data-quant]').each(function() {
                    var $row = $(this);
                    if(variacao_id  == $row.data('variacaoid'))
                        $row.data('quant', quantidade);
                });
            }
        });
        dialogChangeQuantity();
    });
    
    function dialogChangeQuantity(){
        
        if(isQuantidadeAlterada()){
            $('tr[data-quant]').each(function() {
                var $row = $(this);
                var quantidadeOriginal = $row.data('quant');
                var nomeProduto = $row.children('td.nome_produto').children('a').html();
                quantidade             = $row.find('.quantidade').val();            
                variacao_id            = $row.data('variacaoid');
                urlCarrinhoPost        = $(this).data('url');
                urlDestinoContinuar    = $(this).attr('url-destino');
                
    
                if (quantidade != quantidadeOriginal) {
                    quantidadeAlterada = true;
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
            $("#dialogModal2").show();                     
    }

});

