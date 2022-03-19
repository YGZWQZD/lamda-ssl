import torch.nn as nn
import torch.nn.functional as F
import torch


class TextRCNN(nn.Module):

    def __init__(self, n_vocab,embedding_dim=300,len_seq=300, padding_idx=None, hidden_size=256, num_layers=1,
                 dropout=0.0, pretrained_embeddings=None,num_class=2):
        super(TextRCNN, self).__init__()

        if pretrained_embeddings is not None:
            self.embedding = nn.Embedding.from_pretrained(pretrained_embeddings, freeze=False)
        else:
            self.embedding = nn.Embedding(n_vocab, embedding_dim, padding_idx=padding_idx)
        self.lstm = nn.LSTM(embedding_dim, hidden_size, num_layers,
                            bidirectional=True, batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_size * 2 +embedding_dim, hidden_size * 2)
        self.maxpool = nn.MaxPool1d(len_seq)
        self.classfier = nn.Linear(hidden_size * 2, num_class)
        self.dropout = nn.Dropout(dropout)


    def forward(self, x):
        # print(x.dtype)
        x=x.long()
        embed = self.embedding(x)  # [batch_size, seq_len, embeding]=[64, 32, 64]
        # print(embed.shape)# [300,300]
        out, _ = self.lstm(embed)
        # print(out.shape)#[300,512]
        out = torch.cat((embed, out), 2)
        # print(out.shape) # [300,812]
        fc_output = torch.tanh(self.fc(out))   # [batch_size, max_seq_len, hidden_size*2]

        maxpool_input = fc_output.permute(0, 2, 1)  # [batch_size, hidden_size*2, max_seq_len]
        maxpool_output = self.maxpool(maxpool_input).squeeze()   # [batch_size, hidden_size*2]

        cls_input = self.dropout(maxpool_output)
        out = self.classfier(cls_input)

        return out