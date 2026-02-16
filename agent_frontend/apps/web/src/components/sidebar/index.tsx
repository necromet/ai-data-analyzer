import { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import ThreadHistory from "@/components/thread/history";
import DatabaseConnector from "@/components/database/connector";
import DatabaseViewer from "@/components/database/viewer";
import { History, Database, Eye } from "lucide-react";

export default function Sidebar() {
  const [activeTab, setActiveTab] = useState("history");

  return (
    <div className="h-full flex flex-col w-full">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
        <div className="px-4 pt-4">
          <TabsList className="w-full grid grid-cols-3">
            <TabsTrigger value="history" className="flex items-center gap-2">
              <History className="size-4" />
              <span className="hidden sm:inline">History</span>
            </TabsTrigger>
            <TabsTrigger value="connector" className="flex items-center gap-2">
              <Database className="size-4" />
              <span className="hidden sm:inline">Connect</span>
            </TabsTrigger>
            <TabsTrigger value="viewer" className="flex items-center gap-2">
              <Eye className="size-4" />
              <span className="hidden sm:inline">Schema</span>
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="history" className="flex-1 overflow-hidden m-0">
          <ThreadHistory />
        </TabsContent>

        <TabsContent value="connector" className="flex-1 overflow-hidden m-0">
          <DatabaseConnector />
        </TabsContent>

        <TabsContent value="viewer" className="flex-1 overflow-hidden m-0">
          <DatabaseViewer />
        </TabsContent>
      </Tabs>
    </div>
  );
}
