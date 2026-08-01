import os
import logging
import pandas as pd
from tqdm import tqdm
from src.data_loader import load_data_and_context
from src.router import apply_hard_rules, route_message_llm

# Setup Chat Transcript Logging
logging.basicConfig(
    filename='log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def main():
    print("Loading messages and context...")
    messages_df, users_df = load_data_and_context()
    
    results = []
    
    print("Processing messages...")
    for idx, row in tqdm(messages_df.iterrows(), total=len(messages_df)):
        msg_id = row.get("message_id", f"msg_{idx}")
        
        # 1. Hard safety rules check
        pred = apply_hard_rules(row)
        
        # 2. LLM reasoning check if no hard rule triggered
        if not pred:
            try:
                pred = route_message_llm(row)
            except Exception as e:
                pred = {
                    "action": "digest",
                    "message_type": "general",
                    "reason": f"Error during classification: {str(e)}",
                    "confidence": 0.5,
                    "evidence_message_ids": []
                }
            
        pred["message_id"] = msg_id
        
        if isinstance(pred.get("evidence_message_ids"), list):
            pred["evidence_message_ids"] = ",".join(pred["evidence_message_ids"])
            
        results.append(pred)
        
        logging.info(f"Message ID: {msg_id} | Action: {pred['action']} | Reason: {pred['reason']}")

    output_df = pd.DataFrame(results)
    
    template_path = os.path.join("dataset", "output.csv")
    if os.path.exists(template_path):
        template_cols = list(pd.read_csv(template_path).columns)
        output_df = output_df[[col for col in template_cols if col in output_df.columns]]
        
    output_df.to_csv("output.csv", index=False)
    print("Processing completed successfully! Predictions saved to output.csv and log saved to log.txt.")

if __name__ == "__main__":
    main()